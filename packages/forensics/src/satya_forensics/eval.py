"""M6 / P-18 metrics over the synthetic test set (docs/SYNTHETIC-TESTSET-PLAN.md §3, §5.2).

Per rule: precision, recall and false-flag rate on the clean controls (a third of the variants
are "noisy but clean": benign incremental updates, odd signature metadata, a certificate with a
day left, a CRL entry after signing, same-day and one-way-only dates, a visible real signature, a
spaced UDIN). Per document: label accuracy against the generator's expected label. Extraction
accuracy of the fields the stamp, notary, mark and UDIN rules read, against what was printed.

    python -m satya_forensics.eval            # dev + held-out tables
"""

import sys
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date

from satya_affidavit.synth.institutions import DEV_PROFILES, HELD_OUT_PROFILES
from satya_forensics import pki
from satya_forensics.engine import M6Input, M6Result, run
from satya_forensics.registry import Registry
from satya_forensics.rules import load_ruleset
from satya_forensics.signatures import TrustStore
from satya_forensics.stamp import read_notary, read_stamp
from satya_forensics.synth.variants import (
    ACCOUNTS_FILE,
    AFFIDAVIT_FILE,
    VARIANTS,
    M6Case,
    build_case,
    prior_filings,
)
from satya_forensics.textlayer import find_marks, read_pages
from satya_forensics.udin import read_accounts

EVAL_TOKEN_KEY = b"satya-eval-token-key-synthetic-only-0001"
CHECKED_AT = "2026-11-25T10:00:00+05:30"


# OCR-dependent advisory notes are excluded from precision/recall because the metrics corpus has
# no OCR text; they are covered by unit tests instead (services/api/tests/test_ocr_fallback.py).
# Only advisory notes (info severity, preliminary indicator) may be listed here; a test enforces it.
ADVISORY_NOTES_WITHOUT_PLANTED_CASES: frozenset[str] = frozenset({"STAMP-OCR-MATCH"})


def scored_rule_ids(rule_ids: Iterable[str] | None = None) -> list[str]:
    """Rules that enter the metrics: every rule except the named advisory notes."""
    ids = list(load_ruleset().rules) if rule_ids is None else list(rule_ids)
    return [r for r in ids if r not in ADVISORY_NOTES_WITHOUT_PLANTED_CASES]


@dataclass
class RuleScore:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    controls: int = 0
    controls_flagged: int = 0

    @property
    def precision(self) -> float:
        return 1.0 if self.tp + self.fp == 0 else self.tp / (self.tp + self.fp)

    @property
    def recall(self) -> float:
        return 1.0 if self.tp + self.fn == 0 else self.tp / (self.tp + self.fn)

    @property
    def false_flag_rate(self) -> float:
        return 0.0 if self.controls == 0 else self.controls_flagged / self.controls


@dataclass
class Ratio:
    ok: int = 0
    total: int = 0

    @property
    def value(self) -> float:
        return 1.0 if self.total == 0 else self.ok / self.total


@dataclass
class Report:
    name: str
    cases: int = 0
    controls: int = 0
    rules: dict[str, RuleScore] = field(default_factory=lambda: defaultdict(RuleScore))
    labels: Ratio = field(default_factory=Ratio)
    extraction: dict[str, Ratio] = field(default_factory=lambda: defaultdict(Ratio))
    mismatches: list[str] = field(default_factory=list)

    def table(self) -> str:
        lines = [
            f"M6/P-18 metrics: {self.name} ({self.cases} cases, {self.controls} clean controls = "
            f"{self.controls / max(self.cases, 1):.0%})",
            f"{'rule':<22} {'TP':>4} {'FP':>4} {'FN':>4} {'precision':>9} {'recall':>7} {'FFR':>6}",
        ]
        for rule_id in scored_rule_ids():
            s = self.rules[rule_id]
            lines.append(
                f"{rule_id:<22} {s.tp:>4} {s.fp:>4} {s.fn:>4} {s.precision:>9.3f} "
                f"{s.recall:>7.3f} {s.false_flag_rate:>6.3f}"
            )
        ok, total = self.labels.ok, self.labels.total
        lines.append(f"document label accuracy: {self.labels.value:.3f} ({ok}/{total})")
        fields_ = ", ".join(
            f"{k} {v.value:.3f} ({v.ok}/{v.total})" for k, v in sorted(self.extraction.items())
        )
        lines.append(f"extraction: {fields_}")
        return "\n".join(lines)


def run_generated(case: M6Case, registry: Registry | None = None) -> M6Result:
    files = {d["doc_id"]: case.files[d["file"]] for d in case.case["documents"]}
    return run(
        M6Input(
            case=case.case,
            snapshot=case.snapshot,
            files=files,
            token_key=EVAL_TOKEN_KEY,
            trust=TrustStore.test_anchor(),
            revocation=pki.standard_crl_endpoints(list(case.crl_specs)),
            registry=registry or Registry.from_json(prior_filings()),
            checked_at=CHECKED_AT,
        )
    )


def _iso(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def _score_extraction(report: Report, case: M6Case) -> None:
    printed = case.truth["printed"]
    pages = read_pages(case.files[AFFIDAVIT_FILE])
    stamp = read_stamp(pages)
    notary = read_notary(pages, "MM/DD/YYYY")
    got = {
        "stamp.certificate_no": stamp.certificate_no if stamp else None,
        "stamp.second_party": stamp.second_party
        if stamp and stamp.instrument == "e-stamp"
        else None,
        "stamp.duty": stamp.duty_rupees if stamp else None,
        "stamp.issued": _iso(stamp.issued) if stamp else None,
        "notary.date": _iso(notary.notarised) if notary else None,
        "notary.valid_till": _iso(notary.seal_valid_till) if notary else None,
    }
    want = dict(printed)
    if stamp and stamp.instrument != "e-stamp":
        want["stamp.second_party"] = None
    for key, value in got.items():
        ratio = report.extraction[key.split(".")[0]]
        ratio.total += 1
        ratio.ok += int(value == want[key])
    if printed.get("mark.date"):
        marks = find_marks(pages)
        mark_dates = {m.signed_at.date().isoformat() for m in marks if m.signed_at}
        ratio = report.extraction["mark"]
        ratio.total += 1
        ratio.ok += int(printed["mark.date"] in mark_dates)
    acc = read_accounts(read_pages(case.files[ACCOUNTS_FILE]))
    ratio = report.extraction["udin"]
    ratio.total += 2
    ratio.ok += int((acc.udin if acc else None) == printed["udin"])
    ratio.ok += int((acc.membership_no if acc else None) == printed["udin.membership_no"])


def evaluate(cases: Iterable[M6Case], name: str) -> Report:
    report = Report(name)
    rule_ids = scored_rule_ids()
    for case in cases:
        report.cases += 1
        control = bool(case.truth["control"])
        report.controls += int(control)
        result = run_generated(case)
        produced = {(f["rule_id"], f["check_ref"]) for f in result.flags}
        expected = {(f["rule_id"], f["check_ref"]) for f in case.truth["expected_flags"]}
        for rule_id in rule_ids:
            got = {p for p in produced if p[0] == rule_id}
            want = {e for e in expected if e[0] == rule_id}
            score = report.rules[rule_id]
            score.tp += len(got & want)
            score.fp += len(got - want)
            score.fn += len(want - got)
            if control:
                score.controls += 1
                score.controls_flagged += int(bool(got))
        for ref in sorted((produced - expected) | (expected - produced)):
            side = "unexpected" if ref in produced else "missed"
            report.mismatches.append(f"{case.slug}: {side} {ref[1]}")
        for doc in result.documents:
            want_label = case.truth["expected_document_labels"].get(doc.doc_id)
            report.labels.total += 1
            if doc.verification["label"] == want_label:
                report.labels.ok += 1
            else:
                report.mismatches.append(
                    f"{case.slug}: {doc.slot} label {doc.verification['label']} != {want_label}"
                )
        _score_extraction(report, case)
    return report


def corpus(profiles: Iterable[int]) -> list[M6Case]:
    return [build_case(p, v) for p in profiles for v in VARIANTS]


def main() -> int:
    for name, profiles in (("dev seeds", DEV_PROFILES), ("held-out seeds", HELD_OUT_PROFILES)):
        report = evaluate(corpus(profiles), name)
        print(report.table())
        for line in report.mismatches:
            print("  ", line)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
