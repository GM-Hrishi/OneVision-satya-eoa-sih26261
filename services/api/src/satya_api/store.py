"""Inbound event dedupe + ledger append, in Postgres (runtime) or memory (unit tests).

Slice 0 stores no event payloads: only metadata and the SHA-256 of the raw body. Payload storage,
tokenisation and the vault arrive with M2 (P-19).
"""

import asyncio
import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from ulid import ULID

from satya_api.ledger import GENESIS, LedgerRow, chain_hash, detail_text

# Arbitrary constant key for pg_advisory_xact_lock: serialises ledger appends and dedupe.
LEDGER_LOCK_KEY = 0x5A7A_0001


@dataclass(frozen=True)
class InboundEvent:
    event_id: str
    event_type: str
    application_id: str
    ay: str
    sequence: int
    producer: str
    kid: str
    payload_sha256: str


@dataclass(frozen=True)
class RecordResult:
    receipt_id: str
    duplicate: bool
    ledger_seq: int | None


def new_receipt_id() -> str:
    return f"rcp_{ULID()}"


class EventStore(Protocol):
    async def record_inbound(self, event: InboundEvent) -> RecordResult: ...
    async def ledger_rows(self) -> list[LedgerRow]: ...
    async def append(
        self, event_type: str, case_id: str | None, actor: str | None, detail: dict[str, Any]
    ) -> LedgerRow: ...
    async def ping(self) -> None: ...
    async def close(self) -> None: ...


class MemoryStore:
    def __init__(self, dedupe_days: int = 30) -> None:
        self.dedupe = timedelta(days=dedupe_days)
        self.events: dict[str, tuple[str, datetime]] = {}
        self.rows: list[LedgerRow] = []
        self._lock = asyncio.Lock()

    async def record_inbound(self, event: InboundEvent) -> RecordResult:
        async with self._lock:
            now = datetime.now(UTC)
            seen = self.events.get(event.event_id)
            if seen and now - seen[1] < self.dedupe:
                return RecordResult(seen[0], True, None)
            prev = self.rows[-1].hash if self.rows else GENESIS
            row = LedgerRow(
                seq=len(self.rows) + 1,
                at=now,
                event_type=event.event_type,
                payload_sha256=event.payload_sha256,
                prev_hash=prev,
                hash=chain_hash(prev, event.payload_sha256, now),
            )
            self.rows.append(row)
            receipt = new_receipt_id()
            self.events[event.event_id] = (receipt, now)
            return RecordResult(receipt, False, row.seq)

    async def ledger_rows(self) -> list[LedgerRow]:
        return list(self.rows)

    async def append(
        self, event_type: str, case_id: str | None, actor: str | None, detail: dict[str, Any]
    ) -> LedgerRow:
        async with self._lock:
            now = datetime.now(UTC)
            prev = self.rows[-1].hash if self.rows else GENESIS
            text_ = detail_text(event_type, case_id, actor, detail)
            sha = hashlib.sha256(text_.encode()).hexdigest()
            row = LedgerRow(
                len(self.rows) + 1,
                now,
                event_type,
                sha,
                prev,
                chain_hash(prev, sha, now),
                case_id,
                actor,
                text_,
            )
            self.rows.append(row)
            return row

    async def ping(self) -> None:
        return None

    async def close(self) -> None:
        return None


class PostgresStore:
    def __init__(self, url: str, dedupe_days: int = 30) -> None:
        self.engine: AsyncEngine = create_async_engine(url, pool_size=5, pool_pre_ping=True)
        self.dedupe_days = dedupe_days

    async def record_inbound(self, event: InboundEvent) -> RecordResult:
        async with self.engine.begin() as conn:
            await conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": LEDGER_LOCK_KEY})
            await conn.execute(
                text(
                    "DELETE FROM inbound_events WHERE event_id = :id "
                    "AND received_at < now() - make_interval(days => :days)"
                ),
                {"id": event.event_id, "days": self.dedupe_days},
            )
            existing = (
                await conn.execute(
                    text("SELECT receipt_id FROM inbound_events WHERE event_id = :id"),
                    {"id": event.event_id},
                )
            ).scalar_one_or_none()
            if existing:
                return RecordResult(existing, True, None)
            prev = (
                await conn.execute(text("SELECT hash FROM ledger ORDER BY seq DESC LIMIT 1"))
            ).scalar_one_or_none() or GENESIS
            at = datetime.now(UTC)
            seq = (
                await conn.execute(
                    text(
                        "INSERT INTO ledger (at, event_type, payload_sha256, prev_hash, hash) "
                        "VALUES (:at, :type, :sha, :prev, :hash) RETURNING seq"
                    ),
                    {
                        "at": at,
                        "type": event.event_type,
                        "sha": event.payload_sha256,
                        "prev": prev,
                        "hash": chain_hash(prev, event.payload_sha256, at),
                    },
                )
            ).scalar_one()
            receipt = new_receipt_id()
            await conn.execute(
                text(
                    "INSERT INTO inbound_events (event_id, receipt_id, event_type, application_id, "
                    "ay, sequence, producer, kid, payload_sha256, received_at, ledger_seq) VALUES "
                    "(:id, :rcp, :type, :app, :ay, :seq, :producer, :kid, :sha, :at, :lseq)"
                ),
                {
                    "id": event.event_id,
                    "rcp": receipt,
                    "type": event.event_type,
                    "app": event.application_id,
                    "ay": event.ay,
                    "seq": event.sequence,
                    "producer": event.producer,
                    "kid": event.kid,
                    "sha": event.payload_sha256,
                    "at": at,
                    "lseq": seq,
                },
            )
            return RecordResult(receipt, False, seq)

    async def ledger_rows(self) -> list[LedgerRow]:
        async with self.engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT seq, at, event_type, payload_sha256, prev_hash, hash, "
                    "case_id, actor, detail_json FROM ledger ORDER BY seq"
                )
            )
            return [LedgerRow(*row) for row in result.all()]

    async def append(
        self, event_type: str, case_id: str | None, actor: str | None, detail: dict[str, Any]
    ) -> LedgerRow:
        text_ = detail_text(event_type, case_id, actor, detail)
        sha = hashlib.sha256(text_.encode()).hexdigest()
        async with self.engine.begin() as conn:
            await conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": LEDGER_LOCK_KEY})
            prev = (
                await conn.execute(text("SELECT hash FROM ledger ORDER BY seq DESC LIMIT 1"))
            ).scalar_one_or_none() or GENESIS
            at = datetime.now(UTC)
            digest = chain_hash(prev, sha, at)
            seq = (
                await conn.execute(
                    text(
                        "INSERT INTO ledger (at, event_type, payload_sha256, prev_hash, hash, "
                        "case_id, actor, detail_json) VALUES (:at, :type, :sha, :prev, :hash, "
                        ":case, :actor, :detail) RETURNING seq"
                    ),
                    {
                        "at": at,
                        "type": event_type,
                        "sha": sha,
                        "prev": prev,
                        "hash": digest,
                        "case": case_id,
                        "actor": actor,
                        "detail": text_,
                    },
                )
            ).scalar_one()
        return LedgerRow(seq, at, event_type, sha, prev, digest, case_id, actor, text_)

    async def ping(self) -> None:
        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def close(self) -> None:
        await self.engine.dispose()
