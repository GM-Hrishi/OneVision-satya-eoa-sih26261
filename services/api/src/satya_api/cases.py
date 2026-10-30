"""Case repository for the Workbench API.

Serves the synthetic demo cases in `SATYA_DEMO_CASES_DIR` (data/synthetic/cases): each case
directory holds case.json, snapshot.json and its documents (the signed sworn affidavit, the audited
statement). This stands in for the ingest path that later slices build (application.submitted →
M2 vault fetch + hash check → worker run → stored results, P-19/P-17). M5 and M6 results are
computed on first request, off the event loop, one at a time, and cached by document hashes; runs
are deterministic, so the cache never goes stale for the same bytes.

M6 (slice 2) needs three more inputs, all synthetic and read-only, next to the cases folder:
`pki/` (public half of the test PKI: the TEST TRUST ANCHOR root, the sub-CA and its CRL, served by
a mock CRL endpoint) and `registry/prior-filings.json` (earlier filings for the reuse checks). The
register also holds every current case's stamp number and UDIN, read from its documents.
"""

import asyncio
import json
import logging
import re
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from satya_affidavit.engine import CaseInput, run
from satya_affidavit.ids import sha256_hex
from satya_forensics import pki as test_pki
from satya_forensics.engine import M6Input, M6Result
from satya_forensics.engine import run as run_m6
from satya_forensics.labels import label_counts
from satya_forensics.registry import Registry
from satya_forensics.signatures import TrustStore
from satya_forensics.stamp import certificate_number
from satya_forensics.textlayer import read_pages
from satya_forensics.udin import fy_label, read_accounts
from satya_ocr import DocumentRead, OcrEngine, OcrSettings, read_document
from satya_ocr.model import from_dict as read_from_dict
from satya_ocr.model import to_dict as read_to_dict
from satya_shared_types import validator

log = logging.getLogger("satya.cases")

CASE_ID = re.compile(r"^cas_[0-9A-HJKMNP-TV-Z]{26}$")
DOC_ID = re.compile(r"^doc_[0-9A-HJKMNP-TV-Z]{26}$")
MAX_PDF_BYTES = 20 * 1024 * 1024
AFFIDAVIT_SLOT = "annex2.1(i) affidavit"
ACCOUNTS_SLOT = "annex2.1(vii) audited accounts"
M6_SECTIONS = {"stamp", "chronology", "signatures"}
STATE_CODES = {"Tamil Nadu": "TN"}


class CaseError(Exception):
    """A case on disk is unusable (bad JSON, schema failure, hash mismatch)."""


@dataclass(frozen=True)
class CaseSummary:
    case_id: str
    application_id: str
    permanent_id: str | None
    ay: str
    regional_office: str
    institution_name: str | None
    route: str
    stage: str
    category_set: tuple[str, ...]


class CaseRepository(Protocol):
    async def list_cases(self) -> list[CaseSummary]: ...

    async def get(self, case_id: str) -> CaseSummary | None: ...

    async def affidavit_diff(self, case_id: str) -> dict[str, Any]: ...

    async def verification(self, case_id: str) -> dict[str, Any]: ...

    async def open_flags(self, case_id: str) -> int: ...

    async def document_verification(self, case_id: str, doc_id: str) -> dict[str, Any] | None: ...


class FixtureCaseRepository:
    """Synthetic demo cases from a directory (read-only)."""

    def __init__(
        self,
        root: Path | None,
        token_key: bytes,
        concurrency: int = 1,
        pki_dir: Path | None = None,
        registry_file: Path | None = None,
        ocr_engine: OcrEngine | None = None,
        ocr_settings: OcrSettings | None = None,
        ocr_cache_dir: Path | None = None,
    ) -> None:
        self.root = root
        self.token_key = token_key
        self._dirs: dict[str, Path] | None = None
        self._cache: dict[tuple[str, str], dict[str, Any]] = {}
        self._m6: dict[tuple[str, ...], tuple[M6Result, str]] = {}
        self._gate = asyncio.Semaphore(concurrency)
        base = root.parent if root else None
        self.pki_dir = pki_dir or (base / "pki" if base else None)
        self.registry_file = registry_file or (
            base / "registry" / "prior-filings.json" if base else None
        )
        self._registry: Registry | None = None
        # Slice D: documents uploaded through the workbench replace the seeded file of a slot.
        self._overlay: dict[tuple[str, str], dict[str, Any]] = {}
        # B-28: how each file can be read (text layer, OCR, or not at all), cached by SHA-256.
        self.ocr_engine = ocr_engine
        self.ocr_settings = ocr_settings or OcrSettings()
        self._reads: dict[str, DocumentRead] = {}
        self._ocr_gate = threading.Semaphore(1)  # OCR is expensive: one document at a time
        self.ocr_cache_dir = ocr_cache_dir  # the stored OCR text layers, one JSON per file hash

    def read_of(self, data: bytes) -> DocumentRead:
        """Classify and, if needed, OCR a file. Never raises; cached by content hash."""
        sha = sha256_hex(data)
        if sha not in self._reads:
            with self._ocr_gate:
                if sha not in self._reads:
                    self._reads[sha] = self._cached_read(sha, data)
        return self._reads[sha]

    def _cached_read(self, sha: str, data: bytes) -> DocumentRead:
        path = self.ocr_cache_dir / f"{sha}.json" if self.ocr_cache_dir else None
        if path is not None and path.is_file():
            try:
                return read_from_dict(json.loads(path.read_text("utf-8")))
            except (OSError, ValueError, KeyError, TypeError):
                log.warning("ocr cache entry unreadable", extra={"sha256": sha})
        read = read_document(data, self.ocr_settings, self.ocr_engine)
        # Keep the OCR text layer only when OCR ran; "engine missing" must be retried later.
        if path is not None and any(p.ocr for p in read.pages):
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(read_to_dict(read)), "utf-8")
            except OSError:
                log.warning("ocr cache entry not written", extra={"sha256": sha})
        return read

    def set_upload(self, case_id: str, slot: str, entry: dict[str, Any]) -> None:
        """Make `entry` (doc_id, sha256, bytes, uploaded_at, upload_path) the file of a slot."""
        self._overlay[(case_id, slot)] = entry
        self._registry = None  # stamp numbers and UDINs of the register come from the documents

    def clear_uploads(self) -> None:
        self._overlay.clear()
        self._registry = None

    def case_dir(self, case_id: str) -> Path | None:
        return self._index().get(case_id)

    def _index(self) -> dict[str, Path]:
        if self._dirs is None:
            dirs: dict[str, Path] = {}
            if self.root and self.root.is_dir():
                for path in sorted(self.root.iterdir()):
                    meta = path / "case.json"
                    if not meta.is_file():
                        continue
                    try:
                        case_id = json.loads(meta.read_text("utf-8"))["case_id"]
                    except (ValueError, KeyError):
                        log.error("unreadable case.json", extra={"case_dir": path.name})
                        continue
                    if CASE_ID.fullmatch(case_id):
                        dirs[case_id] = path
            self._dirs = dirs
        return self._dirs

    def _read_case(
        self, case_id: str, overlay: bool = True
    ) -> tuple[Path, dict[str, Any], dict[str, Any]]:
        path = self._index()[case_id]
        try:
            case = json.loads((path / "case.json").read_text("utf-8"))
            snapshot = json.loads((path / "snapshot.json").read_text("utf-8"))
        except (OSError, ValueError) as exc:
            raise CaseError("case files unreadable") from exc
        for doc in case.get("documents", []) if overlay else []:
            entry = self._overlay.get((case_id, doc.get("slot", "")))
            if entry:
                doc.update(entry)
        if list(validator("ApplicationSnapshot").iter_errors(snapshot)):
            raise CaseError("snapshot fails ApplicationSnapshot")
        return path, case, snapshot

    @staticmethod
    def _read_document(path: Path, doc: dict[str, Any]) -> bytes:
        name = str(doc.get("file", ""))
        if not name or "/" in name or "\\" in name or name.startswith("."):
            raise CaseError("bad document file name")
        pdf_path = Path(doc["upload_path"]) if doc.get("upload_path") else path / name
        if pdf_path.stat().st_size > MAX_PDF_BYTES:
            raise CaseError("DOC_TOO_LARGE")
        data = pdf_path.read_bytes()
        if sha256_hex(data) != doc["sha256"]:
            raise CaseError("DOC_HASH_MISMATCH")
        return data

    def _load(self, case_id: str) -> tuple[dict[str, Any], dict[str, Any], bytes]:
        path, case, snapshot = self._read_case(case_id)
        doc = next((d for d in case.get("documents", []) if d.get("slot") == AFFIDAVIT_SLOT), None)
        if doc is None:
            raise CaseError("no affidavit document")
        return case, snapshot, self._read_document(path, doc)

    def _load_all(self, case_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, bytes]]:
        path, case, snapshot = self._read_case(case_id)
        files = {d["doc_id"]: self._read_document(path, d) for d in case.get("documents", [])}
        return case, snapshot, files

    def _summary(self, case: dict[str, Any]) -> CaseSummary:
        return CaseSummary(
            case_id=case["case_id"],
            application_id=case["application_id"],
            permanent_id=case.get("permanent_id"),
            ay=case["ay"],
            regional_office=case["regional_office"],
            institution_name=case.get("institution_name"),
            route=case["route"],
            stage=case["stage"],
            category_set=tuple(case.get("category_set", [])),
        )

    async def list_cases(self) -> list[CaseSummary]:
        out = []
        for case_id in self._index():
            summary = await self.get(case_id)
            if summary:
                out.append(summary)
        return out

    async def get(self, case_id: str) -> CaseSummary | None:
        path = self._index().get(case_id)
        if path is None:
            return None
        try:
            case = json.loads((path / "case.json").read_text("utf-8"))
        except (OSError, ValueError) as exc:
            raise CaseError("case.json unreadable") from exc
        return self._summary(case)

    async def case_files(
        self, case_id: str
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, bytes]]:
        return await asyncio.to_thread(self._load_all, case_id)

    async def registry(self) -> Registry:
        if self._registry is None:
            self._registry = await asyncio.to_thread(self._build_registry)
        return self._registry

    async def m5_diff(self, case_id: str) -> dict[str, Any]:
        """The M5 AffidavitDiff alone (M6 sections still null, `pending` lists them)."""
        case, snapshot, pdf = await asyncio.to_thread(self._load, case_id)
        key = (case_id, sha256_hex(pdf))
        if key not in self._cache:
            async with self._gate:
                if key not in self._cache:
                    read = await asyncio.to_thread(self.read_of, pdf)
                    result = await asyncio.to_thread(
                        run,
                        CaseInput(
                            case,
                            snapshot,
                            pdf,
                            self.token_key,
                            ocr=read.layers() or None,
                            unreadable_pages=read.page_count if read.blocked else None,
                        ),
                    )
                    self._cache[key] = {
                        **result.diff,
                        "comparison": comparison_of(read, result.diff),
                    }
        return self._cache[key]

    # ---- M6 (slice 2) --------------------------------------------------------------------------
    def _trust(self) -> tuple[TrustStore, test_pki.MockCrlEndpoints]:
        crls: dict[str, bytes] = {}
        if self.pki_dir and self.pki_dir.is_dir():
            trust = TrustStore.from_pem_dir(self.pki_dir)
            crl = self.pki_dir / "satya-test-sub-ca-1.crl"
            if crl.is_file():
                crls[test_pki.CRL_URL] = crl.read_bytes()
        else:
            trust = TrustStore((), (), test_pki.TRUST_ANCHOR_LABEL)
        return trust, test_pki.MockCrlEndpoints(crls)

    def _build_registry(self) -> Registry:
        """Prior filings + every current case's stamp number and UDIN (read from its documents)."""
        registry = Registry.from_file(self.registry_file)
        for case_id in self._index():
            try:
                case, _, files = self._load_all(case_id)
            except (CaseError, OSError):
                log.error("case unusable for the register", extra={"case_id": case_id})
                continue
            for doc in case.get("documents", []):
                data = files.get(doc["doc_id"])
                if data is None:
                    continue
                read = self.read_of(data)
                if read.blocked:
                    continue
                pages = read_pages(data, read.layers() or None)
                if doc["slot"] == AFFIDAVIT_SLOT:
                    # O-23: only numbers from a native text layer enter the reuse register.
                    number = certificate_number([p for p in pages if not p.from_ocr])
                    if number:
                        registry.add_stamp(number, case["application_id"], case["ay"])
                elif doc["slot"] == ACCOUNTS_SLOT:
                    acc = read_accounts(pages)
                    if acc and acc.udin and acc.fy_end:
                        registry.add_udin(acc.udin, case.get("permanent_id"), fy_label(acc.fy_end))
        return registry

    def _run_m6(self, case_id: str) -> tuple[M6Result, str]:
        case, snapshot, files = self._load_all(case_id)
        if self._registry is None:
            self._registry = self._build_registry()
        trust, crls = self._trust()
        checked_at = datetime.now(UTC).isoformat(timespec="seconds")
        result = run_m6(
            M6Input(
                case=case,
                snapshot=snapshot,
                files=files,
                token_key=self.token_key,
                trust=trust,
                revocation=crls,
                registry=self._registry,
                checked_at=checked_at,
                reads={doc_id: self.read_of(data) for doc_id, data in files.items()},
            )
        )
        return result, checked_at

    async def m6(self, case_id: str) -> tuple[M6Result, str, dict[str, Any]]:
        case, _, files = await asyncio.to_thread(self._load_all, case_id)
        key = (case_id, *sorted(sha256_hex(b) for b in files.values()))
        if key not in self._m6:
            async with self._gate:
                if key not in self._m6:
                    self._m6[key] = await asyncio.to_thread(self._run_m6, case_id)
        result, checked_at = self._m6[key]
        return result, checked_at, case

    async def affidavit_diff(self, case_id: str) -> dict[str, Any]:
        """The M5 diff with M6's stamp, signing order and signature badges filled in."""
        diff = await self.m5_diff(case_id)
        result, _, _ = await self.m6(case_id)
        return merge_m6(diff, result)

    async def open_flags(self, case_id: str) -> int:
        """M5 + M6 findings on the case (every flag is undisposed until M11 records decisions)."""
        diff = await self.m5_diff(case_id)
        result, _, _ = await self.m6(case_id)
        return len({f["flag_id"] for f in diff["flags"]} | {f["flag_id"] for f in result.flags})

    async def verification(self, case_id: str) -> dict[str, Any]:
        result, checked_at, case = await self.m6(case_id)
        return case_verification(case, result, checked_at)

    async def document_verification(self, case_id: str, doc_id: str) -> dict[str, Any] | None:
        result, _, _ = await self.m6(case_id)
        doc = next((d for d in result.documents if d.doc_id == doc_id), None)
        return None if doc is None else doc.verification


def read_note(summary: dict[str, Any]) -> dict[str, Any]:
    """The ReadNote of a document read (DocumentRead.summary()): what the pages carry stays out."""
    return {
        "status": summary["status"],
        "reason_code": summary["reason_code"],
        "variant": summary["variant"],
        "values": summary["values"],
        "ocr_mean_confidence": summary["ocr_mean_confidence"],
    }


# Where the sworn text came from, by the variant of the read (satya_ocr.reasons.WHY).
_COMPARISON_SOURCE = {
    "scan_read": "scan_read",
    "low_confidence": "scan_unreliable",
    "scan_not_attempted": "scan_not_read",
    "scan_timeout": "scan_timeout",
    "unavailable": "ocr_unavailable",
}


def comparison_of(read: DocumentRead, diff: dict[str, Any]) -> dict[str, Any]:
    """Whether the sworn copy was really compared (D1 of B-43).

    Only a file with a text layer is compared. A scan, even one read by OCR, and an unreadable file
    are not: text read by OCR never decides anything (decision #60), so the page must say so.
    `diff` is accepted so the rule can look at the structure result later without a new signature.
    """
    note = read_note(read.summary())
    if read.reason_code is None:
        return {"state": "compared", "source": "text_layer", "read": note}
    source = _COMPARISON_SOURCE.get(read.variant or "", "unreadable")
    return {"state": "not_compared", "source": source, "read": note}


def merge_m6(diff: dict[str, Any], result: M6Result) -> dict[str, Any]:
    """A copy of an AffidavitDiff with the M6 sections (UI §6.3) and the affidavit's M6 flags."""
    section = result.affidavit
    if section is None or section["doc_id"] != diff["doc_id"]:
        return diff
    merged = dict(diff)
    merged["sworn"] = {
        **diff["sworn"],
        "issuer_sig": section["issuer_sig"],
        "uploader_sig": section["uploader_sig"],
    }
    merged["stamp"] = section["stamp"]
    merged["chronology"] = section["chronology"]
    merged["pending"] = [p for p in diff["pending"] if p["section"] not in M6_SECTIONS]
    merged["flags"] = [*diff["flags"], *(f for f in result.flags if f["doc_id"] == diff["doc_id"])]
    return merged


def _actions(label: str, checks: list[dict[str, Any]]) -> list[str]:
    actions = ["recheck"]
    if label in ("source_unavailable", "manual_review_required"):
        actions.append("route_manual")
    if label == "verification_pending" or any(
        c["outcome"] == "source_unavailable" and c.get("attempts") for c in checks
    ):
        actions.append("retry")
    return actions


def case_verification(
    case: dict[str, Any],
    result: M6Result,
    checked_at: str,
    answers: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """RB-06 data (UI §6.4) from an M6 result.

    `answers` maps a doc_id to the label, checks, source and read the Case tab shows (the workflow
    view, which adds the source hub and the scan gating). Without it only the M6 result is used.
    """
    documents = []
    for doc in result.documents:
        answer = (answers or {}).get(doc.doc_id)
        label = answer["label"] if answer else doc.verification["label"]
        checks = answer["checks"] if answer else doc.verification["checks"]
        documents.append(
            {
                "doc_id": doc.doc_id,
                "slot": doc.slot,
                "title": doc.title,
                "format_type": doc.format_type,
                "state_code": STATE_CODES.get(case.get("state", "")),
                "issuer_profile": None,
                "source": answer["source"] if answer else doc.source,
                "label": label,
                "issuer_sig": doc.issuer_sig,
                "uploader_sig": doc.uploader_sig,
                "checked_at": checked_at,
                "response_ref": answer["response_ref"] if answer else doc.response_ref,
                "actions": _actions(label, checks),
                "flag_count": len(doc.flags),
                "checks": checks,
                "flags": doc.flags,
                **({"read": answer["read"]} if answer else {}),
            }
        )
    trust_label = test_pki.TRUST_ANCHOR_LABEL
    return {
        "case_id": case["case_id"],
        "advisory": True,
        "trust_anchor_label": trust_label,
        "last_full_run_at": checked_at,
        "label_counts": label_counts(d["label"] for d in documents),
        "documents": documents,
    }
