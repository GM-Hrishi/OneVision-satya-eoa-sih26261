"""Demo cases (committed under data/synthetic/cases/) and the bulk M5 test corpus."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from satya_affidavit.ids import sha256_hex, stable_id
from satya_affidavit.synth.institutions import PROFILES
from satya_affidavit.synth.variants import VARIANTS, GeneratedCase, generate

# (directory, profile, variant, demo)
DEMO_CASES: tuple[tuple[str, int, str, bool], ...] = (
    ("dit03-2026-27", 3, "demo", True),
    ("dce05-2026-27", 5, "clean", False),
)
SWORN_FILE = "affidavit-sworn.pdf"


def default_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "data" / "synthetic").is_dir() and (parent / "pyproject.toml").is_file():
            return parent / "data" / "synthetic" / "cases"
    raise FileNotFoundError("data/synthetic not found; pass --out")


def _json(data: Any) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def case_files(generated: GeneratedCase) -> dict[str, bytes]:
    case = dict(generated.case)
    case["documents"] = [
        {
            "doc_id": stable_id("doc", sha256_hex(generated.pdf)),
            "slot": "annex2.1(i) affidavit",
            "declared_type": "affidavit-2",
            "file": SWORN_FILE,
            "sha256": sha256_hex(generated.pdf),
            "bytes": len(generated.pdf),
        }
    ]
    return {
        "case.json": _json(case),
        "snapshot.json": _json(generated.snapshot),
        "truth.json": _json(generated.truth),
        SWORN_FILE: generated.pdf,
    }


def _demo() -> Iterator[tuple[str, dict[str, bytes]]]:
    for directory, profile, variant, demo in DEMO_CASES:
        yield directory, case_files(generate(profile, "clean" if demo else variant, demo=demo))


def write_demo_cases(root: Path | None = None) -> list[Path]:
    root = root or default_root()
    written = []
    for directory, files in _demo():
        target = root / directory
        target.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            (target / name).write_bytes(data)
            written.append(target / name)
    return written


def check_demo_cases(root: Path | None = None) -> list[str]:
    root = root or default_root()
    stale = []
    for directory, files in _demo():
        for name, data in files.items():
            path = root / directory / name
            if not path.is_file() or path.read_bytes() != data:
                stale.append(str(path))
    return stale


def bulk_cases() -> Iterator[GeneratedCase]:
    for profile in PROFILES:
        for variant in VARIANTS:
            yield generate(profile, variant)


def write_bulk(root: Path) -> int:
    count = 0
    for generated in bulk_cases():
        target = root / generated.slug
        target.mkdir(parents=True, exist_ok=True)
        for name, data in case_files(generated).items():
            (target / name).write_bytes(data)
        count += 1
    return count
