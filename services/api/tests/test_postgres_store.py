"""PostgresStore against a real, migrated database (CI service container or `make test-db`).

Skipped unless SATYA_TEST_DATABASE_URL (runtime role) is set.
"""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from ulid import ULID

from satya_api.ledger import verify_chain
from satya_api.store import InboundEvent, PostgresStore

URL = os.environ.get("SATYA_TEST_DATABASE_URL")
pytestmark = [
    pytest.mark.anyio,
    pytest.mark.skipif(not URL, reason="needs SATYA_TEST_DATABASE_URL"),
]


def event(event_id: str | None = None) -> InboundEvent:
    return InboundEvent(
        event_id=event_id or f"evt_{ULID()}",
        event_type="application.precheck_requested",
        application_id="1-90000004217",
        ay="2026-27",
        sequence=1,
        producer="mock-portal",
        kid="test-k1",
        payload_sha256="ab" * 32,
    )


@pytest.fixture
async def store():  # type: ignore[no-untyped-def]
    s = PostgresStore(URL or "")
    yield s
    await s.close()


async def test_dedupe_and_chain(store: PostgresStore) -> None:
    ev = event()
    first = await store.record_inbound(ev)
    again = await store.record_inbound(ev)
    assert not first.duplicate and again.duplicate
    assert again.receipt_id == first.receipt_id
    for _ in range(3):
        await store.record_inbound(event())
    assert verify_chain(await store.ledger_rows()).ok


async def test_runtime_role_cannot_update_or_delete_ledger(store: PostgresStore) -> None:
    await store.record_inbound(event())
    for statement in ("UPDATE ledger SET event_type = 'x'", "DELETE FROM ledger"):
        with pytest.raises(DBAPIError):
            async with store.engine.begin() as conn:
                await conn.execute(text(statement))


async def test_runtime_role_cannot_create_tables(store: PostgresStore) -> None:
    with pytest.raises(DBAPIError):
        async with store.engine.begin() as conn:
            await conn.execute(text("CREATE TABLE intruder (id int)"))
