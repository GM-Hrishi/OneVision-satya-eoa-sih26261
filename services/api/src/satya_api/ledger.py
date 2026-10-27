"""Hash-chained ledger: the seed of M12 (P-11).

hash = sha256(prev_hash || payload_sha256 || at), with hex strings and `at` rendered as
UTC ISO 8601 with microseconds (YYYY-MM-DDTHH:MM:SS.ffffffZ), concatenated and UTF-8 encoded.
The first row's prev_hash is 64 zeros.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

GENESIS = "0" * 64


def canonical_at(at: datetime) -> str:
    return at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def chain_hash(prev_hash: str, payload_sha256: str, at: datetime) -> str:
    material = f"{prev_hash}{payload_sha256}{canonical_at(at)}".encode()
    return hashlib.sha256(material).hexdigest()


def canonical_json(obj: Any) -> str:
    """Stable JSON text for ledger details: sorted keys, no spaces, UTF-8 characters kept."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def detail_text(
    event_type: str, case_id: str | None, actor: str | None, detail: dict[str, Any]
) -> str:
    """The exact text hashed into payload_sha256 for workflow entries (Slice D)."""
    return canonical_json(
        {"event_type": event_type, "case_id": case_id, "actor": actor, "detail": detail}
    )


@dataclass(frozen=True)
class LedgerRow:
    seq: int
    at: datetime
    event_type: str
    payload_sha256: str
    prev_hash: str
    hash: str
    # Slice D workflow entries carry their detail text; portal-event rows leave these empty.
    case_id: str | None = None
    actor: str | None = None
    detail_json: str | None = None


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
        if row.detail_json is not None:
            if hashlib.sha256(row.detail_json.encode()).hexdigest() != row.payload_sha256:
                return ChainReport(False, len(rows), row.seq, "detail does not match its hash")
            try:
                head = json.loads(row.detail_json)
            except ValueError:
                return ChainReport(False, len(rows), row.seq, "detail is not valid JSON")
            if (
                head.get("event_type") != row.event_type
                or head.get("case_id") != row.case_id
                or head.get("actor") != row.actor
            ):
                return ChainReport(False, len(rows), row.seq, "detail does not match its columns")
        prev = row.hash
    return ChainReport(True, len(rows))
