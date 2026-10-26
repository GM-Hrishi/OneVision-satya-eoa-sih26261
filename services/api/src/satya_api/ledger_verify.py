"""`python -m satya_api.ledger_verify`: recompute the ledger hash chain; exit 1 if broken."""

import asyncio
import json
import sys

from satya_api.config import get_settings
from satya_api.ledger import verify_chain
from satya_api.store import PostgresStore


async def main() -> int:
    settings = get_settings()
    store = PostgresStore(settings.database_url.get_secret_value())
    try:
        report = verify_chain(await store.ledger_rows())
    finally:
        await store.close()
    print(
        json.dumps(
            {
                "ok": report.ok,
                "rows": report.rows,
                "broken_at": report.broken_at,
                "reason": report.reason,
            }
        )
    )
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
