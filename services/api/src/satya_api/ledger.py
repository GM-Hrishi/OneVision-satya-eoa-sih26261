"""Hash-chained ledger: the seed of M12 (P-11).

hash = sha256(prev_hash || payload_sha256 || at), with hex strings and `at` rendered as
UTC ISO 8601 with microseconds (YYYY-MM-DDTHH:MM:SS.ffffffZ), concatenated and UTF-8 encoded.
The first row's prev_hash is 64 zeros.
"""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

GENESIS = "0" * 64


def canonical_at(at: datetime) -> str:
    return at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def chain_hash(prev_hash: str, payload_sha256: str, at: datetime) -> str:
    material = f"{prev_hash}{payload_sha256}{canonical_at(at)}".encode()
    return hashlib.sha256(material).hexdigest()


@dataclass(frozen=True)
class LedgerRow:
    seq: int
    at: datetime
    event_type: str
    payload_sha256: str
    prev_hash: str
    hash: str


@dataclass(frozen=True)
class ChainReport:
    ok: bool
    rows: int
    broken_at: int | None = None
    reason: str | None = None


def verify_chain(rows: list[LedgerRow]) -> ChainReport:
    prev = GENESIS
    for row in rows:
        if row.prev_hash != prev:
            return ChainReport(False, len(rows), row.seq, "prev_hash does not match previous row")
        if chain_hash(row.prev_hash, row.payload_sha256, row.at) != row.hash:
            return ChainReport(False, len(rows), row.seq, "hash does not match row content")
        prev = row.hash
    return ChainReport(True, len(rows))
