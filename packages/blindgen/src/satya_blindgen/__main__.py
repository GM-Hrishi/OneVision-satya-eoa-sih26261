"""python -m satya_blindgen generate|evaluate (see packages/blindgen/README.md)."""

import argparse
import shutil
import sys
from pathlib import Path

from satya_blindgen.config import load_config
from satya_blindgen.evaluate import evaluate, manifest_sha
from satya_blindgen.generate import generate

DEFAULT_OUT = Path("data/blind")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="satya_blindgen")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("generate", "evaluate", "run"):
        p = sub.add_parser(name)
        p.add_argument("--out", type=Path, default=DEFAULT_OUT)
        p.add_argument("--n", type=int, default=None, help="applications (default: config)")
        p.add_argument("--docs", type=Path, default=Path("docs/eval"))
        p.add_argument("--expect-sha", default=None)
    args = parser.parse_args(argv)
    cfg = load_config(applications=args.n)
    if args.cmd in ("generate", "run"):
        if args.out.exists():
            shutil.rmtree(args.out)
        path = generate(args.out, cfg.seeds, cfg.applications, cfg.clean_fraction_min)
        print(f"manifest {path} sha256 {manifest_sha(path)}")
    if args.cmd in ("evaluate", "run"):
        res = evaluate(args.out, args.docs, args.expect_sha)
        clean = res["clean_applications"]
        print(
            f"{res['applications']} applications, {clean} clean; clean flagged {res['clean_flagged']}/{clean}"
        )
        print(
            f"misses {len(res['misses'])}, false flags {len(res['false_flags'])}, crashes {len(res['crashes'])}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
