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
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from satya_affidavit.ids import sha256_hex
from satya_api.cases import (
    ACCOUNTS_SLOT,
    AFFIDAVIT_SLOT,
    CaseError,
    FixtureCaseRepository,
)
from satya_api.ledger import LedgerRow, verify_chain
from satya_api.sources import apply_hub
from satya_api.store import EventStore
from satya_api.triage import (
    alerts_for,
    case_status,
    flag_order,
    risk_band,
    top_reasons,
    why_sentence,
)
from satya_forensics.labels import label_counts
from satya_forensics.stamp import certificate_number
from satya_forensics.textlayer import read_pages
from satya_forensics.udin import read_accounts

log = logging.getLogger("satya.workflow")

ACTIONS = ("accept", "override", "escalate_clarify", "escalate_refer", "escalate_manual")
SLOTS = {"affidavit": AFFIDAVIT_SLOT, "accounts": ACCOUNTS_SLOT}
FLAG_ID = re.compile(r"^flg_[0-9A-HJKMNP-TV-Z]{26}$")
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MIN_REASON = 10

UPLOADED, CHECKED, SOURCE, TASK, DISPOSED = (
    "document.uploaded",
    "check.run",
    "source.response",
    "manual_task.created",
    "disposition.recorded",
)


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
        docs, tasks = [], []
        for res in m6.documents:
            pages = read_pages(files[res.doc_id])
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
            )
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
                "manual_task": label == "source_unavailable",
                "checked_at": checked_at,
            }
            docs.append(doc)
            if doc["manual_task"]:
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
        labels = [d["label"] for d in docs]
        reasons = top_reasons(flags)
        view = {
            "case_id": case_id,
            "documents": docs,
            "flags": flags,
            "tasks": tasks,
            "label_counts": label_counts(labels),
            "checked_at": checked_at,
            "risk": {
                "band": risk_band(flags, labels),
                "reasons": reasons,
                "note": "The band orders review only. It is not a finding.",
            },
            "engine": {
                "m5": diff.get("engine_version"),
                "m6": m6.engine_version,
                "ruleset_m6": m6.ruleset_version,
            },
        }
        self._views[key] = view
        return view

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
        done = {f["flag_id"] for f in flags if f["disposition"]}
        return {
            **base,
            "flags": flags,
            "status": case_status(flags, done),
            "undisposed_flags": len(flags) - len(done),
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
                        "tag": "MOCK SOURCE",
                        "outcome": resp["outcome"],
                        "reason_code": resp["reason_code"],
                        "response_sha256": resp["response_sha256"],
                    },
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
    async def queue(self, regions_ok: Any) -> list[dict[str, Any]]:
        disposed = await self.dispositions()
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
                }
            )
        return out

    async def alerts(self, regions_ok: Any) -> list[dict[str, Any]]:
        out = []
        for summary in await self.repo.list_cases():
            if not regions_ok(summary.regional_office):
                continue
            v = await self.view(summary.case_id)
            case, _, _ = await self.repo.case_files(summary.case_id)
            today = max(date.fromisoformat(d["uploaded_at"][:10]) for d in case["documents"])
            out.extend(
                alerts_for(
                    {"case_id": summary.case_id, "application_id": summary.application_id}, v, today
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
