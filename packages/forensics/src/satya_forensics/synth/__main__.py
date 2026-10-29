"""Write the synthetic demo cases, registers and the public test PKI. Synthetic data only.

python -m satya_forensics.synth            # data/synthetic/{cases,registry,pki}
python -m satya_forensics.synth --check    # fail if the committed files are stale
"""

import argparse
import sys
from pathlib import Path

from satya_forensics.synth.corpus import DEMO_CASES, SCAN_CASES, check_all, write_all


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m satya_forensics.synth")
    parser.add_argument("--out", type=Path, default=None, help="default data/synthetic")
    parser.add_argument("--check", action="store_true", help="compare a fresh generation")
    args = parser.parse_args(argv)
    if args.check:
        stale = check_all(args.out)
        if stale:
            print("stale synthetic files (run `make synth`):", *stale, sep="\n  ")
            return 1
        total = len(DEMO_CASES) + len(SCAN_CASES)
        print(f"synthetic demo cases, registers and test PKI up to date ({total} cases)")
        return 0
    for path in write_all(args.out):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
