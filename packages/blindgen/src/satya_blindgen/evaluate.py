"""Evaluate the engines over a generated blind set and write the report.

Order matters and is kept in code: phase 1 runs M5 and M6 over every application directory and
stores their output; only then (phase 2) is the sealed manifest opened and the output compared
with it. The manifest hash is checked against the hash recorded when the set was generated.

Everything measured is synthetic data generated for this repository. Nothing here is real AICTE
data and no number here says how the system performs on real filings.
"""

import hashlib
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import satya_forensics.pki as pki
from satya_affidavit.engine import CaseInput
from satya_affidavit.engine import run as run_m5
from satya_forensics.engine import M6Input
from satya_forensics.engine import run as run_m6
from satya_forensics.eval import ADVISORY_NOTES_WITHOUT_PLANTED_CASES
from satya_forensics.registry import Registry
from satya_forensics.signatures import TrustStore
from satya_forensics.stamp import read_notary, read_stamp
from satya_forensics.textlayer import read_pages
from satya_forensics.udin import read_accounts

TOKEN_KEY = b"satya-blind-eval-token-key-synthetic-0001"
CHECKED_AT = "2027-01-15T10:00:00+05:30"
AFF_SLOT, ACC_SLOT = "annex2.1(i) affidavit", "annex2.1(vii) audited accounts"
DISCLAIMER = (
    "Synthetic data, generated for this repository by an independent generator. "
    "Not real AICTE data. The numbers below describe this synthetic set only."
)


def manifest_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _iso(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def run_engines(root: Path) -> dict[str, Any]:
    """Phase 1: engine output per application directory. Does not read the manifest."""
    out: dict[str, Any] = {}
    for app_dir in sorted(p for p in root.iterdir() if (p / "case.json").is_file()):
        case = json.loads((app_dir / "case.json").read_text("utf-8"))
        snapshot = json.loads((app_dir / "snapshot.json").read_text("utf-8"))
        files = {d["doc_id"]: (app_dir / d["file"]).read_bytes() for d in case["documents"]}
        aff = next(d for d in case["documents"] if d["slot"] == AFF_SLOT)
        acc = next(d for d in case["documents"] if d["slot"] == ACC_SLOT)
        entry: dict[str, Any] = {"case_id": case["case_id"], "error": None}
        try:
            m5 = run_m5(CaseInput(case, snapshot, files[aff["doc_id"]], TOKEN_KEY)).diff
            m6 = run_m6(
                M6Input(
                    case=case,
                    snapshot=snapshot,
                    files=files,
                    token_key=TOKEN_KEY,
                    trust=TrustStore.test_anchor(),
                    revocation=pki.standard_crl_endpoints([]),
                    registry=Registry(),
                    checked_at=CHECKED_AT,
                )
            )
            seen: set[tuple[str, str, str]] = set()
            flags = []
            # M5 names its document by content hash; the case names it by doc id.
            for f in [*({**x, "doc_id": aff["doc_id"]} for x in m5["flags"]), *m6.flags]:
                key = (f["doc_id"], f["rule_id"], f["check_ref"])
                if key not in seen:
                    seen.add(key)
                    flags.append(
                        {
                            "doc_id": f["doc_id"],
                            "rule_id": f["rule_id"],
                            "check_ref": f["check_ref"],
                        }
                    )
            entry["flags"] = flags
            entry["labels"] = {d.doc_id: d.verification["label"] for d in m6.documents}
            pages = read_pages(files[aff["doc_id"]])
            stamp, notary = read_stamp(pages), read_notary(pages, "MM/DD/YYYY")
            accounts = read_accounts(read_pages(files[acc["doc_id"]]))
            entry["extracted"] = {
                "stamp.certificate_no": stamp.certificate_no if stamp else None,
                "stamp.duty": stamp.duty_rupees if stamp else None,
                "notary.date": _iso(notary.notarised) if notary else None,
                "notary.valid_till": _iso(notary.seal_valid_till) if notary else None,
                "udin": accounts.udin if accounts else None,
                "udin.membership_no": accounts.membership_no if accounts else None,
            }
        except Exception as exc:  # a crash is a result, not something to hide
            entry["error"] = f"{type(exc).__name__}: {exc}"[:200]
        out[app_dir.name] = entry
    return out


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def _prf(tp: int, fp: int, fn: int) -> tuple[float | None, float | None, float | None]:
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = 2 * p * r / (p + r) if p and r else (0.0 if p is not None and r is not None else None)
    return p, r, f


def score(engine_out: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    """Phase 2: compare per application and rule (a rule either fired on the document or not)."""
    rules: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    seeds: dict[int, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    )
    misses: list[dict[str, str]] = []
    false_flags: list[dict[str, str]] = []
    crashes: list[dict[str, str]] = []
    label = {"ok": 0, "total": 0}
    label_misses: list[str] = []
    extraction: dict[str, dict[str, int]] = defaultdict(lambda: {"ok": 0, "total": 0})
    clean_total = clean_flagged = 0
    clean_detail: list[str] = []
    for app in manifest["applications"]:
        res = engine_out.get(app["app"])
        if res is None or res["error"]:
            crashes.append(
                {"app": app["app"], "cause": (res or {}).get("error") or "no engine output"}
            )
            continue
        produced = {(f["doc_id"], f["rule_id"]) for f in res["flags"]}
        produced = {p for p in produced if p[1] not in ADVISORY_NOTES_WITHOUT_PLANTED_CASES}
        expected = {(d, r) for d, info in app["documents"].items() for r in info["expected_rules"]}
        for doc, rule in produced | expected:
            bucket = (
                "tp"
                if (doc, rule) in produced & expected
                else "fp"
                if (doc, rule) in produced
                else "fn"
            )
            rules[rule][bucket] += 1
            seeds[app["seed"]][rule][bucket] += 1
            if bucket == "fn":
                planted = ", ".join(app["anomalies"])
                misses.append(
                    {
                        "app": app["app"],
                        "rule": rule,
                        "cause": f"planted ({planted}); {rule} did not fire on its document",
                    }
                )
            if bucket == "fp":
                other = (
                    f"application carries: {', '.join(app['anomalies'])}"
                    if app["anomalies"]
                    else "clean application"
                )
                false_flags.append(
                    {
                        "app": app["app"],
                        "rule": rule,
                        "cause": f"{rule} fired but was not planted on this document; {other}",
                    }
                )
        if app["clean"]:
            clean_total += 1
            wrong = sorted(r for _, r in produced)
            if wrong:
                clean_flagged += 1
                clean_detail.append(f"{app['app']}: {', '.join(wrong)}")
        for doc, info in app["documents"].items():
            label["total"] += 1
            got = res["labels"].get(doc)
            if got == info["expected_label"]:
                label["ok"] += 1
            else:
                label_misses.append(
                    f"{app['app']} {info['slot']}: engine {got}, expected {info['expected_label']}"
                )
        for key, want in app["printed"].items():
            extraction[key]["total"] += 1
            extraction[key]["ok"] += int(res["extracted"].get(key) == want)
    table = {}
    for rule, c in sorted(rules.items()):
        p, r, f = _prf(c["tp"], c["fp"], c["fn"])
        table[rule] = {
            **c,
            "precision": p,
            "recall": r,
            "f1": f,
            "recall_ci95": wilson(c["tp"], c["tp"] + c["fn"]),
        }
    spread: dict[str, tuple[float, float] | None] = {}
    for rule in table:
        recalls = []
        for s in seeds.values():
            cc = s.get(rule)
            if cc and cc["tp"] + cc["fn"]:
                recalls.append(cc["tp"] / (cc["tp"] + cc["fn"]))
        spread[rule] = (min(recalls), max(recalls)) if recalls else None
    return {
        "applications": len(manifest["applications"]),
        "clean_applications": clean_total,
        "clean_flagged": clean_flagged,
        "clean_detail": clean_detail,
        "rules": table,
        "recall_spread_across_seeds": spread,
        "label_accuracy": label,
        "label_misses": label_misses,
        "extraction": dict(extraction),
        "misses": misses,
        "false_flags": false_flags,
        "crashes": crashes,
    }


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def write_report(result: dict[str, Any], manifest: dict[str, Any], sha: str, docs: Path) -> None:
    docs.mkdir(parents=True, exist_ok=True)
    total = result["applications"]
    clean = result["clean_applications"]
    lines = [
        "# Blind test set report",
        "",
        f"**{DISCLAIMER}**",
        "",
        f"- Applications: {total} across seeds {manifest['seeds']}; clean (no planted anomaly): {clean} ({clean / max(total, 1):.0%}).",
        f"- Manifest SHA-256 (recorded before evaluation): `{sha}`",
        f"- False-flag rate on clean applications: **{result['clean_flagged']} of {clean}** clean applications wrongly flagged.",
        f"- Engine crashes: {len(result['crashes'])}",
        f"- Document label accuracy: {result['label_accuracy']['ok']}/{result['label_accuracy']['total']}",
        "",
        "## Per rule (presence of the rule on a document; counts are documents)",
        "",
        "| rule | TP | FP | FN | precision | recall | F1 | recall 95% CI (Wilson) | recall range over seeds |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for rule, c in result["rules"].items():
        lo, hi = c["recall_ci95"]
        sp = result["recall_spread_across_seeds"][rule]
        spread = "n/a" if sp is None else f"{sp[0]:.2f} to {sp[1]:.2f}"
        lines.append(
            f"| {rule} | {c['tp']} | {c['fp']} | {c['fn']} | {_pct(c['precision'])} | {_pct(c['recall'])} | {_pct(c['f1'])} | {lo:.2f} to {hi:.2f} | {spread} |"
        )
    lines += [
        "",
        "## Field extraction accuracy",
        "",
        "| field | correct | total | accuracy |",
        "|---|---|---|---|",
    ]
    for key, c in sorted(result["extraction"].items()):
        lines.append(f"| {key} | {c['ok']} | {c['total']} | {c['ok'] / max(c['total'], 1):.3f} |")
    lines += ["", f"## Misses ({len(result['misses'])})", ""]
    lines += [f"- `{m['app']}` {m['rule']}: {m['cause']}" for m in result["misses"]] or ["- none"]
    lines += ["", f"## False flags ({len(result['false_flags'])})", ""]
    lines += [f"- `{m['app']}` {m['rule']}: {m['cause']}" for m in result["false_flags"]] or [
        "- none"
    ]
    lines += ["", "## Clean applications wrongly flagged", ""]
    lines += [f"- {d}" for d in result["clean_detail"]] or ["- none"]
    lines += ["", "## Label differences", ""]
    lines += [f"- {d}" for d in result["label_misses"]] or ["- none"]
    lines += ["", "## Engine crashes", ""]
    lines += [f"- `{c['app']}`: {c['cause']}" for c in result["crashes"]] or ["- none"]
    lines += [
        "",
        "## What this set does not cover",
        "",
        "Land and room reconciliation, stamp reuse, UDIN reuse, revoked and expired certificates, the source-hub verification states and the scan fallback reason codes are not planted by this generator. Rule logic was not changed after seeing these results.",
        "",
    ]
    (docs / "BLIND-REPORT.md").write_text("\n".join(lines), "utf-8")
    (docs / "blind-results.json").write_text(
        json.dumps(
            {"disclaimer": DISCLAIMER, "manifest_sha256": sha, **result}, indent=1, sort_keys=True
        ),
        "utf-8",
    )


def evaluate(root: Path, docs: Path, expect_sha: str | None = None) -> dict[str, Any]:
    engine_out = run_engines(root)  # phase 1: the manifest is not opened yet
    manifest_path = root / "manifest.json"
    sha = manifest_sha(manifest_path)
    if expect_sha and sha != expect_sha:
        raise SystemExit("manifest hash differs from the recorded one: refusing to evaluate")
    manifest = json.loads(manifest_path.read_text("utf-8"))
    result = score(engine_out, manifest)
    clean = sum(1 for a in manifest["applications"] if a["clean"])
    result["clean_applications"] = clean
    write_report(result, manifest, sha, docs)
    return result
