"""Deterministic replay (P-11): re-run a case's rules later and compare with what was recorded.

Read-only. Inputs are the documents in the vault (hash checked against the hashes recorded in the
ledger at the original run), the source answers stored in the ledger (no live or mock lookup is
made again) and the rule pack asked for. The only write is one `case.replay` ledger entry. Output
is advisory data for an official; it changes no status.

Reasons (`reasons[].code`): HASH_MISMATCH (vault document or ledger chain no longer matches its
hash, `ref` names which), NO_ORIGINAL_RECORD / ORIGINAL_UNKNOWN (no run, or a run that predates
rule-pack recording), ORIGINAL_RULES_UNAVAILABLE (the original pack is not in the archive),
RESULT_DIFFERS (replay at the original pack gave other flags or labels), REPLAY_FAILED.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from satya_affidavit.engine import CaseInput
from satya_affidavit.engine import run as run_m5
from satya_affidavit.ids import sha256_hex
from satya_api.cases import AFFIDAVIT_SLOT, CaseError, FixtureCaseRepository
from satya_api.ledger import LedgerRow, verify_chain
from satya_api.rulepacks import UNKNOWN, RulePack, RulePackCatalog
from satya_api.sources import apply_stored
from satya_api.store import EventStore
from satya_api.workflow import CHECKED, flag_record
from satya_forensics.engine import M6Input
from satya_forensics.engine import run as run_m6
from satya_forensics.labels import document_label, label_counts

log = logging.getLogger("satya.replay")
security = logging.getLogger("satya.security")

REPLAYED = "case.replay"
MAX_FLAGS = 500  # response size cap per list; `truncated` says when it applied
MAX_PDF_BYTES = 20 * 1024 * 1024


class VaultMismatchError(Exception):
    def __init__(self, ref: str) -> None:
        super().__init__(ref)
        self.ref = ref


def _key(flag: dict[str, Any]) -> tuple[str, str, str]:
    return (str(flag["doc_id"]), str(flag["rule_id"]), str(flag.get("check_ref")))


def _evidence(flag: dict[str, Any]) -> dict[str, Any]:
    return {
        "doc_id": flag["doc_id"],
        "page": flag.get("page"),
        "evidence_sha256": flag.get("evidence_sha256"),
    }


def diff_flags(original: list[dict[str, Any]], replayed: list[dict[str, Any]]) -> dict[str, Any]:
    """Added / removed / changed, matched by (document, rule, check). Flag ids carry the rule
    version, so they are compared, not used as the match key."""
    before = {_key(f): f for f in original}
    after = {_key(f): f for f in replayed}
    added = [
        {"rule_id": k[1], "evidence": _evidence(after[k]), "replayed": after[k]}
        for k in after
        if k not in before
    ]
    removed = [
        {"rule_id": k[1], "evidence": _evidence(before[k]), "original": before[k]}
        for k in before
        if k not in after
    ]
    changed = []
    for k in before.keys() & after.keys():
        fields = [
            f for f in ("rule_version", "severity", "label") if before[k].get(f) != after[k].get(f)
        ]
        if fields:
            changed.append(
                {
                    "rule_id": k[1],
                    "evidence": _evidence(after[k]),
                    "fields": fields,
                    "original": {f: before[k].get(f) for f in fields},
                    "replayed": {f: after[k].get(f) for f in fields},
                }
            )
    order = lambda item: (item["evidence"]["doc_id"], item["rule_id"])  # noqa: E731
    return {
        "added": sorted(added, key=order),
        "removed": sorted(removed, key=order),
        "changed": sorted(changed, key=order),
    }


def _cap(items: list[Any]) -> tuple[list[Any], bool]:
    return items[:MAX_FLAGS], len(items) > MAX_FLAGS


class Replayer:
    def __init__(
        self,
        repo: FixtureCaseRepository,
        store: EventStore,
        upload_dir: Path | None,
        catalog: RulePackCatalog,
        gate: asyncio.Semaphore | None = None,
    ) -> None:
        self.repo = repo
        self.store = store
        self.upload_dir = upload_dir
        self.catalog = catalog
        self._gate = gate or asyncio.Semaphore(1)

    # ---- vault ---------------------------------------------------------------------------------
    def _vault_files(
        self, case_id: str, hashes: dict[str, str]
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, bytes]]:
        """Documents as they were at the original run; every one is hash checked."""
        path, case, snapshot = self.repo._read_case(case_id, overlay=False)
        files: dict[str, bytes] = {}
        for doc in case.get("documents", []):
            doc_id = doc["doc_id"]
            recorded = hashes.get(doc_id)
            name = str(doc.get("file", ""))
            if not recorded or not name or "/" in name or "\\" in name or name.startswith("."):
                raise VaultMismatchError(doc_id)
            if recorded == doc.get("sha256"):
                location = path / name
            elif self.upload_dir is not None:
                location = self.upload_dir / case_id / f"{recorded}.pdf"
            else:
                raise VaultMismatchError(doc_id)
            try:
                if location.stat().st_size > MAX_PDF_BYTES:
                    raise VaultMismatchError(doc_id)
                data = location.read_bytes()
            except OSError:
                raise VaultMismatchError(doc_id) from None
            if sha256_hex(data) != recorded:
                raise VaultMismatchError(doc_id)
            doc["sha256"] = recorded
            files[doc_id] = data
        return case, snapshot, files

    # ---- engines -------------------------------------------------------------------------------
    def _run(
        self,
        pack: RulePack,
        case: dict[str, Any],
        snapshot: dict[str, Any],
        files: dict[str, bytes],
        registry: Any,
        checked_at: str,
        stored: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, Any]]:
        affidavit = next(d for d in case["documents"] if d["slot"] == AFFIDAVIT_SLOT)
        reads = {doc_id: self.repo.read_of(data) for doc_id, data in files.items()}
        read = reads[affidavit["doc_id"]]
        m5 = run_m5(
            CaseInput(
                case,
                snapshot,
                files[affidavit["doc_id"]],
                self.repo.token_key,
                ocr=read.layers() or None,
                unreadable_pages=read.page_count if read.blocked else None,
                ruleset=pack.m5,
            )
        ).diff
        trust, crls = self.repo._trust()
        m6 = run_m6(
            M6Input(
                case=case,
                snapshot=snapshot,
                files=files,
                token_key=self.repo.token_key,
                trust=trust,
                revocation=crls,
                registry=registry,
                checked_at=checked_at,
                reads=reads,
                ruleset=pack.m6,
            )
        )
        labels: dict[str, str] = {}
        for res in m6.documents:
            doc_read = reads[res.doc_id]
            if doc_read.blocked:  # nothing was read: no identifier, no source answer
                verification = res.verification
            else:
                mine = [x for x in stored if x["doc_id"] == res.doc_id]
                verification, _ = apply_stored(res.verification, res.slot, mine, checked_at)
            if doc_read.status == "ocr_read":  # an OCR-read identifier cannot be verified
                for check in verification["checks"]:
                    if check["kind"] == "source_lookup" and check["outcome"] == "verified":
                        check["outcome"] = "manual_review_required"
                        check["reason_code"] = "SRC_READ_BY_OCR"
                verification["label"] = document_label(verification["checks"])
            labels[res.doc_id] = verification["label"]
        by_id: dict[str, dict[str, Any]] = {}
        for flag in [*m5["flags"], *m6.flags]:
            by_id.setdefault(flag["flag_id"], flag)
        engines = {
            "m5": m5.get("engine_version"),
            "m6": m6.engine_version,
            "ruleset_m5": m5.get("ruleset_version"),
            "ruleset_m6": m6.ruleset_version,
        }
        return [flag_record(f) for f in by_id.values()], labels, engines

    # ---- replay --------------------------------------------------------------------------------
    @staticmethod
    def _original(rows: list[LedgerRow], case_id: str) -> tuple[LedgerRow | None, bool]:
        """(latest check.run of the case, whether it carries a rule pack)."""
        latest = None
        for row in rows:
            if row.event_type == CHECKED and row.case_id == case_id and row.detail_json:
                latest = row
        if latest is None:
            return None, False
        return latest, "rule_pack" in json.loads(latest.detail_json or "{}")["detail"]

    async def replay(self, case_id: str, rule_version: str | None, actor: str) -> dict[str, Any]:
        rows = await self.store.ledger_rows()
        result = await self._compute(rows, case_id, rule_version)
        row = await self.store.append(
            REPLAYED,
            case_id,
            actor,
            {
                "rule_version": result["rule_version"],
                "original_rule_version": result["original"]["rule_version"],
                "original_ledger_seq": result["original"]["ledger_seq"],
                "reproducible": result["reproducible"],
                "reasons": [r["code"] for r in result["reasons"]],
                "added": len(result["diff"]["added"]),
                "removed": len(result["diff"]["removed"]),
                "changed": len(result["diff"]["changed"]),
                "advisory": True,
                "regulatory_effect": "none",
            },
        )
        result["ledger_no"] = row.seq
        return result

    async def _compute(
        self, rows: list[LedgerRow], case_id: str, rule_version: str | None
    ) -> dict[str, Any]:
        reasons: list[dict[str, str]] = []
        out: dict[str, Any] = {
            "case_id": case_id,
            "replayed_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "rule_version": rule_version or UNKNOWN,
            "original": {"rule_version": UNKNOWN, "ledger_seq": None, "engines": None},
            "original_flags": [],
            "replayed_flags": [],
            "diff": {"added": [], "removed": [], "changed": []},
            "identical_to_original": False,
            "reproducible": False,
            "reasons": reasons,
            "truncated": False,
            "advisory": True,
            "regulatory_effect": "none",
        }
        chain = verify_chain(rows)
        if not chain.ok:
            security.warning(
                "replay: ledger chain broken",
                extra={"case_id": case_id, "ledger_seq": chain.broken_at},
            )
            reasons.append({"code": "HASH_MISMATCH", "ref": f"ledger:{chain.broken_at}"})
            return out
        latest, recorded = self._original(rows, case_id)
        if latest is None:
            reasons.append({"code": "NO_ORIGINAL_RECORD", "ref": case_id})
            return out
        detail = json.loads(latest.detail_json or "{}")["detail"]
        out["original"] = {
            "rule_version": detail.get("rule_pack", UNKNOWN),
            "ledger_seq": latest.seq,
            "engines": detail.get("engines"),
        }
        if not recorded:
            reasons.append({"code": "ORIGINAL_UNKNOWN", "ref": f"ledger:{latest.seq}"})
            return out
        original_flags, cut = _cap(detail["flags"])
        out["original_flags"] = original_flags
        out["truncated"] = cut
        wanted = rule_version or detail["rule_pack"]
        out["rule_version"] = wanted
        pack = self.catalog.resolve(wanted)
        if pack is None:
            reasons.append({"code": "ORIGINAL_RULES_UNAVAILABLE", "ref": wanted})
            return out
        try:
            async with self._gate:
                case, snapshot, files = await asyncio.to_thread(
                    self._vault_files, case_id, detail["doc_hashes"]
                )
                registry = await self.repo.registry()
                flags, labels, engines = await asyncio.to_thread(
                    self._run,
                    pack,
                    case,
                    snapshot,
                    files,
                    registry,
                    detail["checked_at"],
                    detail["source_responses"],
                )
        except VaultMismatchError as exc:
            security.warning(
                "replay: vault document hash mismatch",
                extra={"case_id": case_id, "doc_id": exc.ref},
            )
            reasons.append({"code": "HASH_MISMATCH", "ref": exc.ref})
            return out
        except (CaseError, KeyError, ValueError, OSError, StopIteration):
            log.exception("replay failed", extra={"case_id": case_id})
            reasons.append({"code": "REPLAY_FAILED", "ref": case_id})
            return out
        replayed, cut = _cap(flags)
        out["replayed_flags"] = replayed
        out["truncated"] = out["truncated"] or cut
        out["engines"] = engines
        out["label_counts"] = label_counts(labels.values())
        out["diff"] = diff_flags(detail["flags"], flags)
        same_ids = {f["flag_id"] for f in flags} == {f["flag_id"] for f in detail["flags"]}
        same_labels = labels == detail.get("labels")
        d = out["diff"]
        out["identical_to_original"] = (
            same_ids and same_labels and not (d["added"] or d["removed"] or d["changed"])
        )
        if wanted == detail["rule_pack"]:
            if not out["identical_to_original"]:
                reasons.append({"code": "RESULT_DIFFERS", "ref": f"ledger:{latest.seq}"})
            out["reproducible"] = out["identical_to_original"]
        else:
            out["reproducible"] = True  # inputs verified; a different pack was asked for
        return out
