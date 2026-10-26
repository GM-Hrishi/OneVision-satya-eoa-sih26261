"""Write the synthetic M5 demo cases (or a bulk test corpus). Synthetic data only.

python -m satya_affidavit.synth                 # demo cases -> data/synthetic/cases/
python -m satya_affidavit.synth --check         # fail if the committed demo cases are stale
python -m satya_affidavit.synth --bulk DIR      # every profile x variant -> DIR (tests)
"""

import argparse
import sys
from pathlib import Path

from satya_affidavit.synth.corpus import DEMO_CASES, check_demo_cases, write_bulk, write_demo_cases


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m satya_affidavit.synth")
    parser.add_argument(
        "--out", type=Path, default=None, help="demo case root (default data/synthetic/cases)"
    )
    parser.add_argument(
        "--check", action="store_true", help="compare a fresh generation with the files"
    )
    parser.add_argument(
        "--bulk", type=Path, default=None, help="write every profile x variant here"
    )
    args = parser.parse_args(argv)
    if args.bulk:
        count = write_bulk(args.bulk)
        print(f"wrote {count} synthetic cases to {args.bulk}")
        return 0
    if args.check:
        stale = check_demo_cases(args.out)
        if stale:
            print("stale synthetic demo files (run `make synth`):", *stale, sep="\n  ")
            return 1
        print(f"synthetic demo cases up to date ({len(DEMO_CASES)} cases)")
        return 0
    for path in write_demo_cases(args.out):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
