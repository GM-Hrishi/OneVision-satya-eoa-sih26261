"""The bulk M5 test corpus.

The committed demo cases (data/synthetic/cases/) are written by `python -m satya_forensics.synth`
since slice 2, because the sworn copy they serve is signed (M6) and M5 must read the same bytes.
"""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from satya_affidavit.ids import sha256_hex, stable_id
from satya_affidavit.synth.institutions import PROFILES
from satya_affidavit.synth.variants import VARIANTS, GeneratedCase, generate

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
