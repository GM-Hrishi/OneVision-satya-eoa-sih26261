"""Demo cases (data/synthetic/cases/), the shared synthetic registers and the M6 test corpus.

The demo cases are now written here rather than by the M5 generator, because the sworn affidavit
they serve is the signed one: M5 and M6 read the same bytes (same SHA-256, same doc_id).
"""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from satya_affidavit.synth.institutions import PROFILES
from satya_forensics import pki
from satya_forensics.synth.variants import VARIANTS, M6Case, build_case, prior_filings

# (directory, profile, demo)
DEMO_CASES: tuple[tuple[str, int, bool], ...] = (
    ("dit03-2026-27", 3, True),
    ("dce05-2026-27", 5, False),
)
REGISTRY_FILE = "prior-filings.json"
PKI_FILES = ("satya-test-root.pem", "satya-test-sub-ca-1.pem", "satya-test-sub-ca-1.crl")


def synthetic_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "data" / "synthetic").is_dir() and (parent / "pyproject.toml").is_file():
            return parent / "data" / "synthetic"
    raise FileNotFoundError("data/synthetic not found; pass --out")


def _json(data: Any) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def case_files(m6: M6Case) -> dict[str, bytes]:
    return {
        "case.json": _json(m6.case),
        "snapshot.json": _json(m6.snapshot),
        "truth.json": _json(m6.m5_truth),
        "truth-m6.json": _json(m6.truth),
        **m6.files,
    }


def demo_cases() -> list[M6Case]:
    return [build_case(p, "clean", demo=demo) for _, p, demo in DEMO_CASES]


def all_files() -> dict[str, bytes]:
    """Every generated file under data/synthetic, keyed by its path relative to that folder."""
    out: dict[str, bytes] = {}
    specs: list[pki.SignerSpec] = []
    for (directory, _, _), m6 in zip(DEMO_CASES, demo_cases(), strict=True):
        for name, data in case_files(m6).items():
            out[f"cases/{directory}/{name}"] = data
        specs += m6.crl_specs
    out[f"registry/{REGISTRY_FILE}"] = _json(prior_filings())
    pems = pki.certificate_pems()
    out["pki/satya-test-root.pem"] = pems["root"]
    out["pki/satya-test-sub-ca-1.pem"] = pems["sub-ca-1"]
    crl = pki.standard_crl_endpoints(specs).crls[pki.CRL_URL]
    out["pki/satya-test-sub-ca-1.crl"] = crl
    return out


def write_all(root: Path | None = None) -> list[Path]:
    root = root or synthetic_root()
    written = []
    for rel, data in all_files().items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        written.append(path)
    return written


def check_all(root: Path | None = None) -> list[str]:
    root = root or synthetic_root()
    stale = []
    for rel, data in all_files().items():
        path = root / rel
        if not path.is_file() or path.read_bytes() != data:
            stale.append(str(path))
    return stale


def bulk_cases(profiles: tuple[int, ...] | None = None) -> Iterator[M6Case]:
    for profile in profiles or tuple(sorted(PROFILES)):
        for variant in VARIANTS:
            yield build_case(profile, variant)
