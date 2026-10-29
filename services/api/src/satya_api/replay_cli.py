"""`python -m satya_api.replay_cli CASE [--rule-version ID]`: replay a case and print a summary.

Runs inside the api container (`make replay CASE=<id>`). Same service as the endpoint; the only
write is the `case.replay` ledger entry, recorded for the actor `cli`.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from satya_api.cases import CASE_ID, FixtureCaseRepository
from satya_api.config import get_settings
from satya_api.replay import Replayer
from satya_api.rulepacks import RulePackCatalog
from satya_api.store import PostgresStore


async def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="replay")
    parser.add_argument("case_id")
    parser.add_argument("--rule-version", default=None)
    args = parser.parse_args(argv)
    if not CASE_ID.fullmatch(args.case_id):
        print("not a case id")
        return 2
    settings = get_settings()
    root = Path(settings.demo_cases_dir) if settings.demo_cases_dir else None
    repo = FixtureCaseRepository(root, settings.token_key())
    store = PostgresStore(settings.database_url.get_secret_value())
    archive = Path(settings.rules_archive_dir) if settings.rules_archive_dir else None
    upload = Path(settings.upload_dir) if settings.upload_dir else None
    replayer = Replayer(repo, store, upload, RulePackCatalog(archive))
    try:
        if await repo.get(args.case_id) is None:
            print("unknown case")
            return 2
        if args.rule_version and args.rule_version not in replayer.catalog.available():
            print("unknown rule version; available:", ", ".join(replayer.catalog.available()))
            return 2
        res = await replayer.replay(args.case_id, args.rule_version, "cli")
    finally:
        await store.close()
    diff = res["diff"]
    print(f"case          {res['case_id']}")
    print(
        f"original      {res['original']['rule_version']} (ledger {res['original']['ledger_seq']})"
    )
    print(f"replayed at   {res['rule_version']}")
    n_old, n_new = len(res["original_flags"]), len(res["replayed_flags"])
    print(f"flags         original {n_old}, replayed {n_new}")
    print(f"diff          +{len(diff['added'])} -{len(diff['removed'])} ~{len(diff['changed'])}")
    print(f"reproducible  {'yes' if res['reproducible'] else 'no'}")
    for reason in res["reasons"]:
        print(f"reason        {reason['code']} {reason['ref']}")
    print("advisory only: no status or decision was changed")
    return 0 if res["reproducible"] else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
