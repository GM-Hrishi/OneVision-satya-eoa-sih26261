"""`python -m satya_api.demo_seed`: record the intake and first check run of every synthetic case.

Run by `make demo-reset` after the ledger was emptied. Each case gets, in this order:
document.uploaded (one per document, origin "seeded"), source.response (one per mock source
answer), check.run and manual_task.created (one per document without a usable source). The case
data is the same on every reset; only the ledger timestamps and hashes differ.
"""

import asyncio
import json
import sys
from pathlib import Path

from satya_api.cases import FixtureCaseRepository
from satya_api.config import get_settings
from satya_api.store import EventStore, PostgresStore
from satya_api.workflow import Workflow
from satya_ocr import OcrSettings
from satya_ocr.engine import PaddleOcrEngine

SEED_ACTOR = "seed.demo"


async def seed_all(workflow: Workflow) -> list[str]:
    """Seed every case that has no ledger entry yet. Returns the case ids seeded."""
    existing = {row.case_id for row in await workflow.store.ledger_rows() if row.case_id}
    seeded = []
    for summary in await workflow.repo.list_cases():
        if summary.case_id in existing:
            continue
        await workflow.seed_case(summary.case_id, SEED_ACTOR)
        seeded.append(summary.case_id)
    return seeded


def build(store: EventStore) -> Workflow:
    settings = get_settings()
    root = Path(settings.demo_cases_dir) if settings.demo_cases_dir else None
    engine = PaddleOcrEngine() if settings.ocr_engine == "paddle" else None
    repo = FixtureCaseRepository(
        root,
        settings.token_key(),
        ocr_engine=engine,
        ocr_settings=OcrSettings.from_env(),
        ocr_cache_dir=Path(settings.upload_dir) / "_ocr" if settings.upload_dir else None,
    )
    return Workflow(repo, store, Path(settings.upload_dir) if settings.upload_dir else None)


async def main() -> int:
    store = PostgresStore(get_settings().database_url.get_secret_value())
    try:
        seeded = await seed_all(build(store))
    finally:
        await store.close()
    print(json.dumps({"seeded_cases": len(seeded)}))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
