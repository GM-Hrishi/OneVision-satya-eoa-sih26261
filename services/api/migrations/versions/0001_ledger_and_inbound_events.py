"""Hash-chained ledger (M12 seed) and inbound event dedupe.

Revision ID: 0001
Revises:
Create Date: 2026-10-26
"""

import os

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

APP_ROLE = os.environ.get("SATYA_DB_APP_ROLE", "satya_app")


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ledger (
            seq            BIGSERIAL PRIMARY KEY,
            at             TIMESTAMPTZ NOT NULL,
            event_type     TEXT        NOT NULL,
            payload_sha256 CHAR(64)    NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
            prev_hash      CHAR(64)    NOT NULL CHECK (prev_hash ~ '^[0-9a-f]{64}$'),
            hash           CHAR(64)    NOT NULL UNIQUE CHECK (hash ~ '^[0-9a-f]{64}$')
        );
        COMMENT ON TABLE ledger IS
            'Append-only hash chain: hash = sha256(prev_hash || payload_sha256 || at). M12 seed (P-11).';

        CREATE FUNCTION ledger_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'ledger is append-only';
        END;
        $$;
        CREATE TRIGGER ledger_no_update BEFORE UPDATE OR DELETE ON ledger
            FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
        CREATE TRIGGER ledger_no_truncate BEFORE TRUNCATE ON ledger
            FOR EACH STATEMENT EXECUTE FUNCTION ledger_append_only();

        CREATE TABLE inbound_events (
            event_id       TEXT        PRIMARY KEY,
            receipt_id     TEXT        NOT NULL UNIQUE,
            event_type     TEXT        NOT NULL,
            application_id TEXT        NOT NULL,
            ay             TEXT        NOT NULL,
            sequence       INTEGER     NOT NULL,
            producer       TEXT        NOT NULL,
            kid            TEXT        NOT NULL,
            payload_sha256 CHAR(64)    NOT NULL,
            received_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            ledger_seq     BIGINT      NOT NULL REFERENCES ledger (seq)
        );
        CREATE INDEX inbound_events_received_at ON inbound_events (received_at);
        COMMENT ON TABLE inbound_events IS
            'Dedupe on event_id for 30 days (Portal spec 2.11). Metadata only; no payloads in slice 0.';
        """
    )
    # Runtime role: read + append only. No UPDATE anywhere; DELETE only for the 30-day dedupe purge.
    op.execute(f"GRANT SELECT, INSERT ON ledger TO {APP_ROLE}")
    op.execute(f"GRANT USAGE ON SEQUENCE ledger_seq_seq TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT, DELETE ON inbound_events TO {APP_ROLE}")


def downgrade() -> None:
    op.execute("DROP TABLE inbound_events")
    op.execute("DROP TABLE ledger")
    op.execute("DROP FUNCTION ledger_append_only()")
