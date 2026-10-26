"""M5 metrics over the synthetic test set (docs/SYNTHETIC-TESTSET-PLAN.md §3, §5.1).

Per rule: precision, recall, false-flag rate on clean controls, and the extraction accuracy of the
fields the rule depends on (compared with what the generator printed, not with the snapshot).

    python -m satya_affidavit.eval            # dev + held-out tables
"""

import sys
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from satya_affidavit.engine import CaseInput, EngineResult, run
from satya_affidavit.normalise import canonical, parse_date, parse_number, squash
from satya_affidavit.rules import load_ruleset
from satya_affidavit.synth.institutions import DEV_PROFILES, HELD_OUT_PROFILES
from satya_affidavit.synth.variants import VARIANTS, GeneratedCase, generate

EVAL_TOKEN_KEY = b"satya-eval-token-key-synthetic-only-0001"
RULE_FIELDS = {
    "AFF-CAT-LINE": ("categories",),
    "AFF-DECL-MISSING": ("declarations",),
    "AFF-DECL-CHANGED": ("declarations",),
    "AFF-DECL-ADDED": ("declarations",),
    "AFF-HEADER": ("header",),
    "LAND-AREA-RECON": ("land",),
    "LAND-ROW-RECON": ("land",),
    "ROOM-RECON": ("rooms",),
    "ROOM-ID-DUP": ("rooms",),
}


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
class FieldScore:
    correct: int = 0
    total: int = 0

    @property
    def accuracy(self) -> float:
        return 1.0 if self.total == 0 else self.correct / self.total


@dataclass
class Report:
    name: str
    cases: int = 0
    rules: dict[str, RuleScore] = field(default_factory=lambda: defaultdict(RuleScore))
    fields: dict[str, FieldScore] = field(default_factory=lambda: defaultdict(FieldScore))
    mismatches: list[str] = field(default_factory=list)

    def table(self) -> str:
        lines = [
            f"M5 metrics: {self.name} ({self.cases} sworn affidavits)",
            f"{'rule':<18} {'TP':>4} {'FP':>4} {'FN':>4} {'precision':>9} {'recall':>7} "
            f"{'FFR':>6} {'extraction':>10}",
        ]
        for rule_id in load_ruleset().rules:
            s = self.rules[rule_id]
            acc = self.extraction(rule_id)
            lines.append(
                f"{rule_id:<18} {s.tp:>4} {s.fp:>4} {s.fn:>4} {s.precision:>9.3f} {s.recall:>7.3f} "
                f"{s.false_flag_rate:>6.3f} {acc:>10.3f}"
            )
        overall = ", ".join(
            f"{k} {v.accuracy:.3f} ({v.correct}/{v.total})" for k, v in sorted(self.fields.items())
        )
        lines.append(f"extraction by field group: {overall}")
        return "\n".join(lines)

    def extraction(self, rule_id: str) -> float:
        groups = RULE_FIELDS[rule_id]
        correct = sum(self.fields[g].correct for g in groups)
        total = sum(self.fields[g].total for g in groups)
        return 1.0 if total == 0 else correct / total


def _score_extraction(report: Report, result: EngineResult, printed: dict[str, Any]) -> None:
    doc = result.sworn
    if doc is None:
        return
    entities = result.draft.entities()
    order = result.draft.template.date_order
    header = report.fields["header"]
    for key in (
        "pid",
        "aid",
        "institution_name",
        "address",
        "institution_type",
        "region",
        "application_date",
    ):
        header.total += 1
        got = doc.header.get(key)
        header.correct += int(
            got is not None and squash(got.text) == squash(printed[f"header.{key}"])
        )
    header.total += 1
    header.correct += int(
        doc.ay_text is not None and squash(doc.ay_text) == squash(printed["header.ay_line"])
    )
    cats = report.fields["categories"]
    cats.total += 1
    cats.correct += int(
        [squash(c.text) for c in doc.categories] == [squash(c) for c in printed["categories"]]
    )
    decls = report.fields["declarations"]
    want = printed["declarations"]
    for i, text in enumerate(want):
        decls.total += 1
        if i < len(doc.declarations):
            a, _ = canonical(doc.declarations[i].text, entities)
            b, _ = canonical(text, entities)
            decls.correct += int(squash(a) == squash(b))

    def cell_equal(got: str | None, printed_cell: str, kind: str) -> bool:
        if kind == "number":
            return parse_number(got) == parse_number(printed_cell)
        if kind == "date":
            return parse_date(got, order)[0] == parse_date(printed_cell, order)[0]
        return squash(got or "") == squash(printed_cell)

    land = report.fields["land"]
    land_kinds = ("text", "text", "date", "text", "text", "number")
    rows = doc.tables["land"].rows
    printed_land = [v for k, v in sorted(printed.items()) if k.startswith("land.")]
    for i, cells in enumerate(printed_land):
        for j, value in enumerate(cells):
            land.total += 1
            if i < len(rows) and j < len(rows[i].cells):
                land.correct += int(cell_equal(rows[i].cells[j], value, land_kinds[j]))
    rooms = report.fields["rooms"]
    room_kinds = ("text", "text", "number", "text", "text", "text")
    for table in ("room_admin", "room_amenities", "room_instructional", "room_common"):
        rows = doc.tables[table].rows
        for i, cells in enumerate(printed[table]):
            for j, value in enumerate(cells):
                rooms.total += 1
                if i < len(rows) and j < len(rows[i].cells):
                    rooms.correct += int(cell_equal(rows[i].cells[j], value, room_kinds[j]))


def evaluate(cases: Iterable[GeneratedCase], name: str) -> Report:
    report = Report(name)
    rule_ids = list(load_ruleset().rules)
    for case in cases:
        report.cases += 1
        result = run(CaseInput(case.case, case.snapshot, case.pdf, EVAL_TOKEN_KEY))
        produced = {(f["rule_id"], f["check_ref"]) for f in result.diff["flags"]}
        expected = {(f["rule_id"], f["check_ref"]) for f in case.truth["expected_flags"]}
        for rule_id in rule_ids:
            got = {p for p in produced if p[0] == rule_id}
            want = {e for e in expected if e[0] == rule_id}
            score = report.rules[rule_id]
            score.tp += len(got & want)
            score.fp += len(got - want)
            score.fn += len(want - got)
            if case.truth["control"]:
                score.controls += 1
                score.controls_flagged += int(bool(got))
        for ref in sorted((produced - expected) | (expected - produced)):
            side = "unexpected" if ref in produced else "missed"
            report.mismatches.append(f"{case.slug}: {side} {ref[1]}")
        _score_extraction(report, result, case.truth["printed"])
    return report


def corpus(profiles: Iterable[int]) -> list[GeneratedCase]:
    return [generate(p, v) for p in profiles for v in VARIANTS]


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
