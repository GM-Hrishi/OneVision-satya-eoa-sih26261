"""Workflow entries on the ledger (Slice D): case id, actor and the hashed detail text.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-26
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The append-only triggers guard UPDATE/DELETE/TRUNCATE only; adding nullable columns is DDL.
    op.execute(
        """
        ALTER TABLE ledger
            ADD COLUMN case_id     TEXT,
            ADD COLUMN actor       TEXT,
            ADD COLUMN detail_json TEXT;
        CREATE INDEX ledger_case_id ON ledger (case_id) WHERE case_id IS NOT NULL;
        COMMENT ON COLUMN ledger.detail_json IS
            'Canonical JSON of {event_type, case_id, actor, detail}; payload_sha256 = sha256(detail_json).';
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX ledger_case_id")
    op.execute("ALTER TABLE ledger DROP COLUMN detail_json, DROP COLUMN actor, DROP COLUMN case_id")
