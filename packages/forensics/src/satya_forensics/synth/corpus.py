"""Demo cases (data/synthetic/cases/), the shared synthetic registers and the M6 test corpus.

The demo cases are now written here rather than by the M5 generator, because the sworn affidavit
they serve is the signed one: M5 and M6 read the same bytes (same SHA-256, same doc_id).
"""

import json
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

from satya_affidavit.ids import sha256_hex, stable_id
from satya_affidavit.synth.institutions import PROFILES
from satya_forensics import pki
from satya_forensics.synth.variants import (
    AFFIDAVIT_FILE,
    VARIANTS,
    M6Case,
    build_case,
    prior_filings,
)
from satya_ocr.synth import SCAN_VARIANTS, rasterise

# (directory, profile, M6 variant, demo story). Slice D (demo flow) adds three planted cases.
DEMO_CASES: tuple[tuple[str, int, str, bool], ...] = (
    ("dit03-2026-27", 3, "clean", True),  # flagship: M5 findings + image-only mark + no UDIN
    ("dce05-2026-27", 5, "clean", False),  # clean control
    ("dit11-2026-27", 11, "stamp_reused", False),  # e-stamp number reused from a prior filing
    ("dce07-2026-27", 7, "udin_length", False),  # UDIN structure problem
    ("dce09-2026-27", 9, "sig_expired", False),  # issuer certificate expired at signing
)
# B-28 scan cases: a clean affidavit rasterised (OCR reads it), a noisy low quality scan (falls back
# to OCR_LOW_CONFIDENCE) and a mixed file (page 2 is an image, the others keep their text layer).
SCAN_CASES: tuple[tuple[str, int, str], ...] = (
    ("dit13-2026-27", 13, "scan_clean"),
    ("dce15-2026-27", 15, "scan_noisy"),
    ("dit17-2026-27", 17, "scan_mixed"),
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


def scan_case(profile: int, kind: str) -> M6Case:
    """A clean synthetic case whose sworn affidavit is replaced by a scan of itself (Pillow)."""
    m6 = build_case(profile, "clean")
    params = dict(SCAN_VARIANTS[kind])
    only = {2} if kind == "scan_mixed" else None
    scan = rasterise(m6.files[AFFIDAVIT_FILE], only_pages=only, **params)  # type: ignore[arg-type]
    old = m6.case["documents"][0]
    new = {**old, "sha256": sha256_hex(scan), "bytes": len(scan)}
    new["doc_id"] = stable_id("doc", new["sha256"])
    m6.case["documents"][0] = new
    files = {**m6.files, AFFIDAVIT_FILE: scan}
    truth = json.loads(json.dumps(m6.truth))
    truth["variant"] = kind
    truth["control"] = False
    truth["scan"] = {"kind": kind, **{k: v for k, v in params.items() if k != "seed"}}
    # The scan has no signature and no M6 finding is planted: only the reading outcome is expected.
    truth["expected_flags"] = []
    truth["expected_checks"] = []
    truth["expected_document_labels"] = {new["doc_id"]: "manual_review_required"}
    return replace(m6, files=files, variant=kind, truth=truth)


def demo_cases() -> list[M6Case]:
    base = [build_case(p, variant, demo=demo) for _, p, variant, demo in DEMO_CASES]
    return base + [scan_case(p, kind) for _, p, kind in SCAN_CASES]


def all_files() -> dict[str, bytes]:
    """Every generated file under data/synthetic, keyed by its path relative to that folder."""
    out: dict[str, bytes] = {}
    specs: list[pki.SignerSpec] = []
    directories = [d for d, *_ in DEMO_CASES] + [d for d, *_ in SCAN_CASES]
    for directory, m6 in zip(directories, demo_cases(), strict=True):
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
