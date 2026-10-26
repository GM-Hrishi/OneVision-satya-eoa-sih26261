"""Case repository for the Workbench API.

Slice 1 serves the synthetic demo cases in `SATYA_DEMO_CASES_DIR` (data/synthetic/cases): each case
directory holds case.json, snapshot.json and the sworn affidavit PDF. This stands in for the ingest
path that later slices build (application.submitted → M2 vault fetch + hash check → worker run →
stored results, P-19/P-17). The M5 result is computed on first request, off the event loop, and
cached by document hash; runs are deterministic, so the cache never goes stale for the same bytes.
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from satya_affidavit.engine import CaseInput, run
from satya_affidavit.ids import sha256_hex
from satya_shared_types import validator

log = logging.getLogger("satya.cases")

CASE_ID = re.compile(r"^cas_[0-9A-HJKMNP-TV-Z]{26}$")
MAX_PDF_BYTES = 20 * 1024 * 1024
AFFIDAVIT_SLOT = "annex2.1(i) affidavit"


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


class FixtureCaseRepository:
    """Synthetic demo cases from a directory (read-only)."""

    def __init__(self, root: Path | None, token_key: bytes, concurrency: int = 1) -> None:
        self.root = root
        self.token_key = token_key
        self._dirs: dict[str, Path] | None = None
        self._cache: dict[tuple[str, str], dict[str, Any]] = {}
        self._gate = asyncio.Semaphore(concurrency)

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

    def _load(self, case_id: str) -> tuple[dict[str, Any], dict[str, Any], bytes]:
        path = self._index()[case_id]
        try:
            case = json.loads((path / "case.json").read_text("utf-8"))
            snapshot = json.loads((path / "snapshot.json").read_text("utf-8"))
        except (OSError, ValueError) as exc:
            raise CaseError("case files unreadable") from exc
        if list(validator("ApplicationSnapshot").iter_errors(snapshot)):
            raise CaseError("snapshot fails ApplicationSnapshot")
        doc = next((d for d in case.get("documents", []) if d.get("slot") == AFFIDAVIT_SLOT), None)
        if doc is None or "/" in doc["file"] or "\\" in doc["file"]:
            raise CaseError("no affidavit document")
        pdf_path = path / doc["file"]
        if pdf_path.stat().st_size > MAX_PDF_BYTES:
            raise CaseError("DOC_TOO_LARGE")
        pdf = pdf_path.read_bytes()
        if sha256_hex(pdf) != doc["sha256"]:
            raise CaseError("DOC_HASH_MISMATCH")
        return case, snapshot, pdf

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

    async def affidavit_diff(self, case_id: str) -> dict[str, Any]:
        case, snapshot, pdf = await asyncio.to_thread(self._load, case_id)
        key = (case_id, sha256_hex(pdf))
        if key not in self._cache:
            async with self._gate:
                if key not in self._cache:
                    result = await asyncio.to_thread(
                        run, CaseInput(case, snapshot, pdf, self.token_key)
                    )
                    self._cache[key] = result.diff
        return self._cache[key]
