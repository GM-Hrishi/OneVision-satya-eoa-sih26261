"""Demo workflow (Slice D): checks, source hub, risk band, dispositions, uploads, audit.

State lives in the hash-chained ledger: uploads, check runs, source responses, manual tasks and
dispositions are ledger entries (event types below). Seeded and uploaded documents are looked at by
the same M5 and M6 engines; nothing here is scored by a model. Advisory only: the five dispositions
are observations and change no regulatory status.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from satya_affidavit.ids import sha256_hex
from satya_api.cases import (
    ACCOUNTS_SLOT,
    AFFIDAVIT_SLOT,
    CaseError,
    FixtureCaseRepository,
    case_verification,
    read_note,
)
from satya_api.ledger import LedgerRow, verify_chain
from satya_api.sources import SOURCES, apply_hub
from satya_api.store import EventStore
from satya_api.triage import (
    BAND_RANK,
    STATUSES,
    alerts_for,
    case_status,
    flag_order,
    risk_band,
    top_reasons,
    why_sentence,
)
from satya_forensics.labels import document_label, label_counts
from satya_forensics.stamp import certificate_number
from satya_forensics.textlayer import read_pages
from satya_forensics.udin import read_accounts

log = logging.getLogger("satya.workflow")

ACTIONS = ("accept", "override", "escalate_clarify", "escalate_refer", "escalate_manual")
SLOTS = {"affidavit": AFFIDAVIT_SLOT, "accounts": ACCOUNTS_SLOT}
FLAG_ID = re.compile(r"^flg_[0-9A-HJKMNP-TV-Z]{26}$")
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MIN_REASON = 10

UPLOADED, CHECKED, SOURCE, TASK, DISPOSED, READ, NOTE = (
    "document.uploaded",
    "check.run",
    "source.response",
    "manual_task.created",
    "disposition.recorded",
    "document.read",
    "document.note",
)


def flag_record(flag: dict[str, Any]) -> dict[str, Any]:
    """The part of a flag the ledger keeps for replay (P-11): identity, rule, version, evidence."""
    return {
        "flag_id": flag["flag_id"],
        "doc_id": flag["doc_id"],
        "rule_id": flag["rule_id"],
        "rule_version": flag["rule_version"],
        "check_ref": flag.get("check_ref"),
        "severity": flag.get("severity"),
        "label": flag.get("label"),
        "page": flag.get("page"),
        "evidence_sha256": flag.get("evidence_sha256"),
    }


class WorkflowError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def validate_pdf(filename: str, data: bytes) -> None:
    """Allow-list by extension and content: .pdf name, %PDF- header, %%EOF trailer, size cap."""
    if not re.fullmatch(r"[\w .()-]{1,120}\.pdf", filename or "", re.I):
        raise WorkflowError("UPLOAD_NAME_REJECTED")
    if len(data) == 0 or len(data) > MAX_UPLOAD_BYTES:
        raise WorkflowError("UPLOAD_SIZE_REJECTED")
    if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-2048:]:
        raise WorkflowError("UPLOAD_CONTENT_REJECTED")


class Workflow:
    def __init__(
        self, repo: FixtureCaseRepository, store: EventStore, upload_dir: Path | None
    ) -> None:
        self.repo = repo
        self.store = store
        self.upload_dir = upload_dir
        self._views: dict[tuple[str, ...], dict[str, Any]] = {}
        self._loaded = False

    # ---- startup -------------------------------------------------------------------------------
    async def restore_uploads(self) -> None:
        """Re-apply uploaded documents from the ledger (latest per case and slot)."""
        if self._loaded:
            return
        self._loaded = True
        latest: dict[tuple[str, str], dict[str, Any]] = {}
        for row in await self.store.ledger_rows():
            if row.event_type == UPLOADED and row.detail_json:
                d = json.loads(row.detail_json)["detail"]
                if d.get("origin") in ("upload", "picked"):
                    latest[(str(row.case_id), d["slot"])] = d
        for (case_id, slot), d in latest.items():
            path = self._upload_path(case_id, d["sha256"])
            if path and path.is_file():
                self.repo.set_upload(case_id, slot, self._entry(d, path))

    def _upload_path(self, case_id: str, sha: str) -> Path | None:
        return self.upload_dir / case_id / f"{sha}.pdf" if self.upload_dir else None

    @staticmethod
    def _entry(d: dict[str, Any], path: Path) -> dict[str, Any]:
        return {
            "sha256": d["sha256"],
            "bytes": d["size"],
            "upload_path": str(path),
            "file": f"{d['sha256']}.pdf",
        }

    async def warm(self) -> None:
        """Compute every case once, in the background, so the first queue request is fast."""
        for summary in await self.repo.list_cases():
            try:
                await self.analyse(summary.case_id)
            except Exception:  # a broken case must not stop the others
                log.exception("warm-up failed", extra={"case_id": summary.case_id})

    # ---- analysis ------------------------------------------------------------------------------
    async def analyse(self, case_id: str) -> dict[str, Any]:
        """Documents with hub results, flags with why sentences and the band (no dispositions)."""
        case, _, files = await self.repo.case_files(case_id)
        key = (case_id, *sorted(sha256_hex(b) for b in files.values()))
        if key in self._views:
            return self._views[key]
        diff = await self.repo.m5_diff(case_id)
        m6, checked_at, _ = await self.repo.m6(case_id)
        merged = await self.repo.affidavit_diff(case_id)
        registry = await self.repo.registry()
        docs: list[dict[str, Any]] = []
        tasks: list[dict[str, Any]] = []
        reads = {res.doc_id: self.repo.read_of(files[res.doc_id]) for res in m6.documents}
        responses: list[dict[str, Any]]
        for res in m6.documents:
            read = reads[res.doc_id]
            if read.blocked:  # nothing was read, so no identifier can be looked up at a source
                verification, responses = res.verification, []
                stamp_no, acc = None, None
            else:
                pages = read_pages(files[res.doc_id], read.layers() or None)
                stamp_no = certificate_number(pages) if res.slot == AFFIDAVIT_SLOT else None
                acc = read_accounts(pages) if res.slot == ACCOUNTS_SLOT else None
                verification, responses = apply_hub(
                    res.verification,
                    res.slot,
                    stamp_no,
                    acc.udin if acc else None,
                    registry,
                    case["application_id"],
                    case["ay"],
                    checked_at,
                    ocr_number=stamp_no is not None
                    and certificate_number([p for p in pages if not p.from_ocr]) is None,
                )
            if read.status == "ocr_read":
                # The identifier was read by OCR, so a matching source answer cannot verify it.
                for check in verification["checks"]:
                    if check["kind"] == "source_lookup" and check["outcome"] == "verified":
                        check["outcome"] = "manual_review_required"
                        check["reason_code"] = "SRC_READ_BY_OCR"
                verification["label"] = document_label(verification["checks"])
            label = verification["label"]
            source = dict(res.source)
            if responses:
                src = responses[-1]["source"]
                source = {"channel": src["adapter_id"], "adapter_mode": src["mode"]}
            meta = next(d for d in case["documents"] if d["doc_id"] == res.doc_id)
            doc = {
                "doc_id": res.doc_id,
                "slot": res.slot,
                "title": res.title,
                "sha256": meta["sha256"],
                "bytes": meta.get("bytes"),
                "label": label,
                "source": source,
                "issuer_sig": res.issuer_sig,
                "uploader_sig": res.uploader_sig,
                "checks": verification["checks"],
                "responses": responses,
                "manual_task": label == "source_unavailable" or read.needs_review,
                "read": read.summary(),
                "checked_at": checked_at,
            }
            docs.append(doc)
            if read.needs_review:
                tasks.append({"doc_id": res.doc_id, "title": res.title, "reason": read.reason_code})
            elif doc["manual_task"]:
                tasks.append(
                    {
                        "doc_id": res.doc_id,
                        "title": res.title,
                        "reason": next(
                            (
                                c["reason_code"]
                                for c in verification["checks"]
                                if c["outcome"] == "source_unavailable"
                            ),
                            "SRC_NO_CHANNEL",
                        ),
                    }
                )
        titles = {d["doc_id"]: d["title"] for d in docs}
        by_id: dict[str, dict[str, Any]] = {}
        for flag in [*diff["flags"], *merged["flags"], *m6.flags]:
            by_id.setdefault(flag["flag_id"], flag)
        flags = []
        for flag in sorted(by_id.values(), key=flag_order):
            flags.append(
                {**flag, "why": why_sentence(flag), "doc_title": titles.get(flag["doc_id"], "")}
            )
        # A scan is not evidence of wrongdoing: its manual review label and the signature findings
        # that follow from having no signature do not raise the band (decision O-5).
        scans = {d["doc_id"] for d in docs if d["read"]["reason_code"]}
        labels = [d["label"] for d in docs]
        band_labels = [d["label"] for d in docs if d["doc_id"] not in scans]
        band_flags = [
            f
            for f in flags
            if f["rule_id"] != "STAMP-OCR-MATCH"  # O-23: a low-trust note, never a band reason
            and not (f["doc_id"] in scans and f["rule_id"].startswith("SIG-"))
        ]
        reasons = top_reasons(band_flags)
        view = {
            "case_id": case_id,
            "documents": docs,
            "flags": flags,
            "tasks": tasks,
            "label_counts": label_counts(labels),
            "checked_at": checked_at,
            "risk": {
                "band": risk_band(band_flags, band_labels),
                "reasons": reasons,
                "note": "The band orders review only. It is not a finding.",
            },
            "engine": {
                "m5": diff.get("engine_version"),
                "m6": m6.engine_version,
                "ruleset_m5": diff.get("ruleset_version"),
                "ruleset_m6": m6.ruleset_version,
            },
        }
        self._views[key] = view
        return view

    async def verification(self, case_id: str) -> dict[str, Any]:
        """RB-06 data from the same view as the Case tab (one source of truth for labels, D4)."""
        view = await self.analyse(case_id)
        m6, checked_at, case = await self.repo.m6(case_id)
        answers = {
            d["doc_id"]: {
                "label": d["label"],
                "checks": d["checks"],
                "source": d["source"],
                "response_ref": d["responses"][-1]["response_sha256"] if d["responses"] else None,
                "read": read_note(d["read"]),
            }
            for d in view["documents"]
        }
        return case_verification(case, m6, checked_at, answers)

    async def document_verification(self, case_id: str, doc_id: str) -> dict[str, Any] | None:
        """VerificationResult of one document, with the label and checks the Case tab shows."""
        view = await self.analyse(case_id)
        doc = next((d for d in view["documents"] if d["doc_id"] == doc_id), None)
        if doc is None:
            return None
        m6, _, _ = await self.repo.m6(case_id)
        res = next(r for r in m6.documents if r.doc_id == doc_id)
        return {**res.verification, "label": doc["label"], "checks": doc["checks"]}

    async def dispositions(self) -> dict[tuple[str, str], dict[str, Any]]:
        out: dict[tuple[str, str], dict[str, Any]] = {}
        for row in await self.store.ledger_rows():
            if row.event_type == DISPOSED and row.detail_json:
                d = json.loads(row.detail_json)["detail"]
                out[(str(row.case_id), d["flag_id"])] = {
                    "action": d["action"],
                    "reason": d["reason"],
                    "by_role": d["by_role"],
                    "by_user_ref": row.actor,
                    "at": row.at.isoformat(),
                    "ledger_no": row.seq,
                }
        return out

    async def view(
        self, case_id: str, disposed: dict[tuple[str, str], dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        base = await self.analyse(case_id)
        disposed = disposed if disposed is not None else await self.dispositions()
        flags = [{**f, "disposition": disposed.get((case_id, f["flag_id"]))} for f in base["flags"]]
        decisions = {f["flag_id"]: f["disposition"]["action"] for f in flags if f["disposition"]}
        return {
            **base,
            "flags": flags,
            "status": case_status(flags, decisions),
            "undisposed_flags": len(flags) - len(decisions),
        }

    # ---- writes (all go through the ledger) ----------------------------------------------------
    async def record_check(self, case_id: str, actor: str, trigger: str) -> dict[str, Any]:
        view = await self.analyse(case_id)
        for doc in view["documents"]:
            for resp in doc["responses"]:
                await self.store.append(
                    SOURCE,
                    case_id,
                    actor,
                    {
                        "doc_id": doc["doc_id"],
                        "adapter_id": resp["source"]["adapter_id"],
                        "source_name": resp["source"]["name"],
                        "tag": "simulated source",
                        "outcome": resp["outcome"],
                        "reason_code": resp["reason_code"],
                        "response_sha256": resp["response_sha256"],
                    },
                )
        for flag in view["flags"]:
            if flag["rule_id"] == "STAMP-OCR-MATCH":  # O-23: low-trust note, not a reuse finding
                await self.store.append(
                    NOTE,
                    case_id,
                    actor,
                    {
                        "doc_id": flag["doc_id"],
                        "rule_id": flag["rule_id"],
                        "note": "Stamp number read by OCR matches another case. "
                        "Needs human verification.",
                        "preliminary_indicator": True,
                    },
                )
        for doc in view["documents"]:
            if doc["read"]["reason_code"]:  # scans and unreadable files: page classes, reason
                await self.store.append(
                    READ,
                    case_id,
                    actor,
                    {"doc_id": doc["doc_id"], "sha256": doc["sha256"], **doc["read"]},
                )
        await self.store.append(
            CHECKED,
            case_id,
            actor,
            {
                "trigger": trigger,
                "engines": view["engine"],
                "labels": {d["doc_id"]: d["label"] for d in view["documents"]},
                "flag_count": len(view["flags"]),
                "risk_band": view["risk"]["band"],
                "flags_sha256": hashlib.sha256(
                    json.dumps(sorted(f["flag_id"] for f in view["flags"])).encode()
                ).hexdigest(),
                # Replay (P-11): what a later run is compared with. Older entries lack these
                # fields and read as `unknown`.
                "rule_pack": f"{view['engine']['ruleset_m5']}+{view['engine']['ruleset_m6']}",
                "checked_at": view["checked_at"],
                "doc_hashes": {d["doc_id"]: d["sha256"] for d in view["documents"]},
                "flags": [flag_record(f) for f in view["flags"]],
                "source_responses": [
                    {
                        "doc_id": d["doc_id"],
                        "adapter_id": r["source"]["adapter_id"],
                        "outcome": r["outcome"],
                        "reason_code": r["reason_code"],
                        "response_sha256": r["response_sha256"],
                    }
                    for d in view["documents"]
                    for r in d["responses"]
                ],
                "advisory": True,
                "regulatory_effect": "none",
            },
        )
        for task in view["tasks"]:
            await self.store.append(
                TASK,
                case_id,
                actor,
                {**task, "queue": "RB-09 manual verification", "reason": task["reason"]},
            )
        return view

    async def seed_case(self, case_id: str, actor: str) -> None:
        case, _, files = await self.repo.case_files(case_id)
        for doc in case["documents"]:
            await self.store.append(
                UPLOADED,
                case_id,
                actor,
                {
                    "doc_id": doc["doc_id"],
                    "slot": doc["slot"],
                    "filename": doc["file"],
                    "sha256": doc["sha256"],
                    "size": len(files[doc["doc_id"]]),
                    "origin": "seeded",
                },
            )
        await self.record_check(case_id, actor, "seed")

    async def upload(
        self,
        case_id: str,
        slot_key: str,
        filename: str,
        data: bytes,
        actor: str,
        origin: str = "upload",
        source_case: str | None = None,
    ) -> dict[str, Any]:
        slot = SLOTS.get(slot_key)
        if slot is None:
            raise WorkflowError("UPLOAD_SLOT_REJECTED")
        validate_pdf(filename, data)
        path = self._upload_path(case_id, sha256_hex(data))
        if path is None:
            raise WorkflowError("UPLOAD_NOT_CONFIGURED")
        case, _, _ = await self.repo.case_files(case_id)
        doc = next(d for d in case["documents"] if d["slot"] == slot)
        sha = sha256_hex(data)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        previous = self.repo._overlay.get((case_id, slot))
        entry = {"sha256": sha, "bytes": len(data), "upload_path": str(path), "file": f"{sha}.pdf"}
        self.repo.set_upload(case_id, slot, entry)
        try:
            await self.analyse(case_id)
        except Exception:  # unreadable or hostile PDF: roll back, log detail server-side only
            log.exception("uploaded pdf could not be checked", extra={"case_id": case_id})
            if previous:
                self.repo.set_upload(case_id, slot, previous)
            else:
                self.repo._overlay.pop((case_id, slot), None)
            path.unlink(missing_ok=True)
            raise WorkflowError("UPLOAD_UNREADABLE") from None
        await self.store.append(
            UPLOADED,
            case_id,
            actor,
            {
                "doc_id": doc["doc_id"],
                "slot": slot,
                "filename": filename,
                "sha256": sha,
                "size": len(data),
                "origin": origin,
                "source_case": source_case,
            },
        )
        await self.record_check(case_id, actor, "upload")
        return await self.view(case_id)

    async def pick(
        self, case_id: str, slot_key: str, source_case: str, actor: str
    ) -> dict[str, Any]:
        """Use the seeded document of another synthetic case in this case's slot."""
        slot = SLOTS.get(slot_key)
        src_dir = self.repo.case_dir(source_case)
        if slot is None or src_dir is None:
            raise WorkflowError("UPLOAD_SLOT_REJECTED")
        meta = json.loads((src_dir / "case.json").read_text("utf-8"))
        doc = next((d for d in meta["documents"] if d["slot"] == slot), None)
        if doc is None:
            raise WorkflowError("UPLOAD_SLOT_REJECTED")
        data = (src_dir / doc["file"]).read_bytes()
        if sha256_hex(data) != doc["sha256"]:
            raise WorkflowError("UPLOAD_CONTENT_REJECTED")
        return await self.upload(case_id, slot_key, doc["file"], data, actor, "picked", source_case)

    async def disposition(
        self, case_id: str, flag_id: str, action: str, reason: str, actor: str, role: str
    ) -> dict[str, Any]:
        if action not in ACTIONS:
            raise WorkflowError("DISPOSITION_ACTION_REJECTED")
        reason = reason.strip()
        if len(reason) < MIN_REASON or len(reason) > 4000:
            raise WorkflowError("DISPOSITION_REASON_REJECTED")
        view = await self.analyse(case_id)
        flag = next((f for f in view["flags"] if f["flag_id"] == flag_id), None)
        if flag is None:
            raise WorkflowError("FLAG_NOT_FOUND")
        row = await self.store.append(
            DISPOSED,
            case_id,
            actor,
            {
                "flag_id": flag_id,
                "rule_id": flag["rule_id"],
                "action": action,
                "reason": reason,
                "by_role": role,
                "advisory": True,
                "regulatory_effect": "none",
            },
        )
        return {
            "action": action,
            "reason": reason,
            "by_role": role,
            "by_user_ref": actor,
            "at": row.at.isoformat(),
            "ledger_no": row.seq,
        }

    # ---- reads ---------------------------------------------------------------------------------
    async def queue(
        self, regions_ok: Any, sort: str | None = None, direction: str | None = None
    ) -> list[dict[str, Any]]:
        """Queue rows, risk band groups first (High, Medium, Low), `sort` applied within each group.

        `sort` is one of QUEUE_SORTS (default: undisposed_flags, descending); `direction` is
        asc or desc (default asc, or desc for the default sort).
        """
        disposed = await self.dispositions()
        first: dict[str, str] = {}
        last: dict[str, str] = {}
        for row in await self.store.ledger_rows():
            if row.case_id:
                stamp = row.at.isoformat()
                first.setdefault(row.case_id, stamp)
                last[row.case_id] = stamp
        out = []
        for summary in await self.repo.list_cases():
            if not regions_ok(summary.regional_office):
                continue
            try:
                v = await self.view(summary.case_id, disposed)
            except CaseError:
                log.exception("case unusable", extra={"case_id": summary.case_id})
                continue
            out.append(
                {
                    "case_id": summary.case_id,
                    "application_id": summary.application_id,
                    "region": summary.regional_office,
                    "ay": summary.ay,
                    "route": summary.route,
                    "stage": summary.stage,
                    "category_set": list(summary.category_set),
                    "institution_name": summary.institution_name,
                    "open_flags": len(v["flags"]),
                    "undisposed_flags": v["undisposed_flags"],
                    "risk_band": v["risk"]["band"],
                    "top_reasons": v["risk"]["reasons"],
                    "label_counts": v["label_counts"],
                    "status": v["status"],
                    "manual_tasks": len(v["tasks"]),
                    "submitted_at": first.get(summary.case_id) or self._fixture_time(v),
                    "last_activity_at": last.get(summary.case_id) or self._fixture_time(v),
                }
            )
        return sort_queue(out, sort, direction)

    @staticmethod
    def _fixture_time(view: dict[str, Any]) -> str:
        """Fallback when the ledger holds nothing for a case: the time of its last check run."""
        return str(view["checked_at"])

    async def overview(
        self, regions_ok: Any, ay: str, region: str | None, now: datetime | None = None
    ) -> dict[str, Any]:
        """Counts for the Overview page. Same case scope as the queue; derived, never typed in."""
        now = now or datetime.now(UTC)
        disposed = await self.dispositions()
        rows = await self.store.ledger_rows()
        task_at: dict[tuple[str, str], datetime] = {}
        for row in rows:
            if row.event_type == TASK and row.case_id and row.detail_json:
                doc_id = json.loads(row.detail_json)["detail"].get("doc_id")
                task_at.setdefault((row.case_id, str(doc_id)), row.at)
        cases: dict[str, str] = {}
        by_band = dict.fromkeys(BAND_RANK, 0)
        status = dict.fromkeys(STATUSES, 0)
        by_label = dict.fromkeys(LABELS, 0)
        tasks: list[dict[str, Any]] = []
        expiring: list[dict[str, Any]] = []
        answers: dict[str, list[str]] = {}
        for summary in await self.repo.list_cases():
            if summary.ay != ay or not regions_ok(summary.regional_office):
                continue
            if region and region != "national" and summary.regional_office.casefold() != region:
                continue
            try:
                v = await self.view(summary.case_id, disposed)
                case, _, _ = await self.repo.case_files(summary.case_id)
            except CaseError:
                log.exception("case unusable", extra={"case_id": summary.case_id})
                continue
            cases[summary.case_id] = summary.application_id
            by_band[v["risk"]["band"]] += 1
            status[v["status"]] += 1
            today = max(date.fromisoformat(d["uploaded_at"][:10]) for d in case["documents"])
            for doc in v["documents"]:
                by_label[doc["label"]] += 1
                for check in doc["checks"]:
                    src = check.get("source")
                    if src:
                        answers.setdefault(src["adapter_id"], []).append(check["outcome"])
                left = [
                    (date.fromisoformat(c["valid_to"]) - today).days
                    for c in doc["checks"]
                    if c.get("valid_to")
                ]
                days = min((d for d in left if d >= 0), default=None)
                if days is not None and days <= EXPIRY_WINDOWS[-1]:
                    valid_to = today + timedelta(days=days)
                    expiring.append(
                        {
                            "doc_type": doc["slot"],
                            "doc_title": doc["title"],
                            "case_id": summary.case_id,
                            "application_id": summary.application_id,
                            "valid_to": valid_to.isoformat(),
                            "days_left": days,
                        }
                    )
            for task in v["tasks"]:
                started = task_at.get((summary.case_id, task["doc_id"]))
                tasks.append(
                    {
                        "case_id": summary.case_id,
                        "application_id": summary.application_id,
                        "reason_key": task["reason"],
                        "age_days": max(0, (now - started).days) if started else 0,
                    }
                )
        tasks.sort(key=lambda t: (-t["age_days"], t["application_id"]))
        expiring.sort(key=lambda e: (e["days_left"], e["application_id"]))
        decisions = []
        for row in reversed(rows):
            if row.event_type != DISPOSED or row.case_id not in cases or not row.detail_json:
                continue
            d = json.loads(row.detail_json)["detail"]
            decisions.append(
                {
                    "at": row.at.isoformat(),
                    "case_id": row.case_id,
                    "application_id": cases[row.case_id],
                    "flag_id": d["flag_id"],
                    "action": d["action"],
                    "by_role": d["by_role"],
                    "ledger_no": row.seq,
                }
            )
            if len(decisions) == OVERVIEW_RECENT:
                break
        return {
            "as_of": now.isoformat(timespec="seconds"),
            "ay": ay,
            "region": region,
            "route": "self_disclosure",
            "cases": {"submitted": len(cases), "by_band": by_band},
            "status": status,
            "documents": {"total": sum(by_label.values()), "by_label": by_label},
            "manual_tasks": {
                "open": len(tasks),
                "oldest_age_days": tasks[0]["age_days"] if tasks else 0,
                "top": tasks[:OVERVIEW_TOP],
            },
            "expiring": {
                **{
                    f"d{w}": sum(1 for e in expiring if e["days_left"] <= w) for w in EXPIRY_WINDOWS
                },
                "top": expiring[:OVERVIEW_TOP],
            },
            "recent_decisions": decisions,
            "sources": [
                {
                    "adapter_id": s["adapter_id"],
                    "name_key": s["name_key"],
                    "mode": s["mode"],
                    "status": (
                        "unavailable"
                        if answers.get(s["adapter_id"])
                        and all(o == "source_unavailable" for o in answers[s["adapter_id"]])
                        else "answering"
                    ),
                }
                for s in SOURCES
            ],
            "advisory": True,
        }

    async def alerts(self, regions_ok: Any) -> list[dict[str, Any]]:
        out = []
        checked_at: dict[str, str] = {}
        for row in await self.store.ledger_rows():
            if row.case_id and row.event_type == CHECKED:
                checked_at[row.case_id] = row.at.isoformat()
        for summary in await self.repo.list_cases():
            if not regions_ok(summary.regional_office):
                continue
            v = await self.view(summary.case_id)
            case, _, _ = await self.repo.case_files(summary.case_id)
            today = max(date.fromisoformat(d["uploaded_at"][:10]) for d in case["documents"])
            out.extend(
                alerts_for(
                    {"case_id": summary.case_id, "application_id": summary.application_id},
                    v,
                    today,
                    checked_at.get(summary.case_id, ""),
                )
            )
        rank = {"suspected_anomaly": 0, "expired": 1, "pending_source": 2}
        return sorted(out, key=lambda a: (rank.get(a["type"], 9), a["application_id"]))

    async def audit(self, case_id: str | None, visible: Any = None) -> dict[str, Any]:
        rows = await self.store.ledger_rows()
        report = verify_chain(rows)
        shown = [
            r
            for r in rows
            if (case_id is None or r.case_id == case_id) and (visible is None or visible(r.case_id))
        ]
        return {
            "chain": {
                "ok": report.ok,
                "rows": report.rows,
                "broken_at": report.broken_at,
                "reason": report.reason,
                "recomputed_at": datetime.now(UTC).isoformat(timespec="seconds"),
                "method": "sha256(prev_hash || payload_sha256 || at), recomputed for every row",
            },
            "entries": [entry(r) for r in reversed(shown)],
        }

    async def audit_entry(self, seq: int) -> dict[str, Any] | None:
        rows = await self.store.ledger_rows()
        row = next((r for r in rows if r.seq == seq), None)
        return (
            None
            if row is None
            else {
                **entry(row),
                "detail": json.loads(row.detail_json)["detail"] if row.detail_json else None,
                "prev_hash": row.prev_hash,
                "hash": row.hash,
                "payload_sha256": row.payload_sha256,
            }
        )


OVERVIEW_TOP = 5
OVERVIEW_RECENT = 8
EXPIRY_WINDOWS = (30, 60, 90)
LABELS = (
    "mismatch_detected",
    "expired",
    "manual_review_required",
    "source_unavailable",
    "verification_pending",
    "verified",
)

QUEUE_SORTS = ("application_id", "undisposed_flags", "submitted_at", "last_activity_at")
QUEUE_DIRS = ("asc", "desc")


def sort_queue(
    rows: list[dict[str, Any]], sort: str | None, direction: str | None
) -> list[dict[str, Any]]:
    """Risk band groups in order, then `sort` inside each group (ties by application id)."""
    key = sort or "undisposed_flags"
    reverse = (direction == "desc") if direction else sort is None
    ordered = sorted(rows, key=lambda r: str(r["application_id"]))
    ordered = sorted(ordered, key=lambda r: r[key], reverse=reverse)
    return sorted(ordered, key=lambda r: BAND_RANK[str(r["risk_band"])])


def entry(row: LedgerRow) -> dict[str, Any]:
    detail = json.loads(row.detail_json)["detail"] if row.detail_json else None
    return {
        "detail": detail,
        "seq": row.seq,
        "at": row.at.isoformat(),
        "event_type": row.event_type,
        "case_id": row.case_id,
        "actor": row.actor,
        "hash": row.hash,
        "payload_sha256": row.payload_sha256,
    }
