"""Clean controls and planted anomalies for M5 (docs/SYNTHETIC-TESTSET-PLAN.md §5.1).

Each variant changes the snapshot (what the institution entered in the portal) and/or the print
model (what the sworn copy prints) and writes down exactly what it planted. That record is the
ground truth; the engine never sees it.
"""

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from satya_affidavit.normalise import ay_long
from satya_affidavit.rules import load_ruleset
from satya_affidavit.synth.institutions import Institution, institution
from satya_affidavit.synth.render import (
    PrintDecl,
    PrintModel,
    Seg,
    Style,
    build_print_model,
    render,
)
from satya_affidavit.template import Draft, draft_header, load_template, render_draft

CONTROL_STYLES: dict[str, Style] = {
    "clean": Style(name="plain"),
    "clean_hyphenated": Style(
        name="hyphenated", hyphenate=True, font_size=11.5, margin_right=110.0
    ),
    "clean_alt_options": Style(name="alt_options", alt_options=True, font_size=10.0),
    "clean_spacing_case": Style(
        name="spacing_case",
        upper_names=True,
        impossible_month_dates=True,
        compact_numbers=True,
        font_size=11.0,
        margin_left=64.0,
    ),
}
PLANTED = (
    "cat_line_missing",
    "decl_dropped",
    "clause_narrowed",
    "decl_inserted",
    "header_ay_stale",
    "land_area_changed",
    "land_row_changed",
    "room_values_changed",
    "room_ids_duplicated",
)
VARIANTS = (*CONTROL_STYLES, *PLANTED)

# Phrase narrowings that keep the sentence grammatical: (old words, new words) per declaration.
NARROWINGS: dict[int, tuple[list[str], list[str]]] = {
    9: (["contiguous", "and", "undisputed,"], ["contiguous,"]),
    6: (
        ["norms", "and", "the", "faculty", "to", "student", "ratio", "prescribed"],
        ["norms", "prescribed"],
    ),
    7: (["institution", "only."], ["institution."]),
    2: (
        ["Council", "and", "has", "not", "shifted", "to", "any", "other", "location."],
        ["Council."],
    ),
    8: (["certificates", "or", "other", "original", "documents", "of"], ["certificates", "of"]),
    13: (["modes,", "and", "no", "capitation", "fee", "is", "charged."], ["modes."]),
}
INSERTED_DECLARATION = (
    "The institution may admit students in excess of the approved intake where seats in other "
    "programmes remain vacant."
)


@dataclass(frozen=True)
class TruthFlag:
    rule_id: str
    key: str
    extracted_value: Any
    expected_value: Any
    value_unit: str | None = None
    page_key: str | None = None

    @property
    def check_ref(self) -> str:
        return f"m5:{self.rule_id}:{self.key}"


@dataclass
class Plan:
    snapshot: list[Callable[[dict[str, Any]], list[TruthFlag]]] = field(default_factory=list)
    printed: list[Callable[[PrintModel, Draft, Style], list[TruthFlag]]] = field(
        default_factory=list
    )


@dataclass(frozen=True)
class GeneratedCase:
    slug: str
    case: dict[str, Any]
    snapshot: dict[str, Any]
    pdf: bytes
    truth: dict[str, Any]
    # Page of every keyed element and the printed signature mark box (used by the M6 generator).
    positions: dict[str, int] = field(default_factory=dict)
    mark_box: tuple[int, float, float, float, float] | None = None


@dataclass(frozen=True)
class Hooks:
    """Extension points for other modules' generators (M6 adds stamp fields and a printed mark).

    `case` runs on the case metadata before the print model is built; `model` runs on the print
    model after the M5 plants and before rendering. Neither may touch what M5 compares.
    """

    case: Callable[[dict[str, Any], dict[str, Any]], None] | None = None
    model: Callable[[PrintModel], None] | None = None


def _all_decls(model: PrintModel) -> list[PrintDecl]:
    return [*model.core, *model.existing]


def _cat_line_missing(model: PrintModel, draft: Draft, style: Style) -> list[TruthFlag]:
    model.categories = []
    return [
        TruthFlag(
            "AFF-CAT-LINE",
            "category_line",
            None,
            "; ".join(draft.category_list),
            page_key="category_line",
        )
    ]


def _decl_dropped(no: int) -> Callable[[PrintModel, Draft, Style], list[TruthFlag]]:
    def mutate(model: PrintModel, draft: Draft, style: Style) -> list[TruthFlag]:
        target = f"decl:{no}"
        model.core = [d for d in model.core if d.key != target]
        model.existing = [d for d in model.existing if d.key != target]
        model.renumber()
        return [TruthFlag("AFF-DECL-MISSING", target, None, draft.declarations[no - 1].display)]

    return mutate


def _clause_narrowed(no: int) -> Callable[[PrintModel, Draft, Style], list[TruthFlag]]:
    def mutate(model: PrintModel, draft: Draft, style: Style) -> list[TruthFlag]:
        old, new = NARROWINGS[no]
        decl = next(d for d in _all_decls(model) if d.key == f"decl:{no}")
        words = [s.text for s in decl.segments]
        for i in range(len(words) - len(old) + 1):
            if words[i : i + len(old)] == old:
                decl.segments[i : i + len(old)] = [Seg(w) for w in new]
                break
        else:
            raise ValueError(f"narrowing for decl {no} not found")
        return [
            TruthFlag(
                "AFF-DECL-CHANGED",
                f"decl:{no}",
                decl.kept_text(),
                draft.declarations[no - 1].display,
            )
        ]

    return mutate


def _decl_inserted(model: PrintModel, draft: Draft, style: Style) -> list[TruthFlag]:
    index = next(i for i, d in enumerate(model.core) if d.key == "decl:12") + 1
    model.core.insert(
        index, PrintDecl("decl:added", 0, "core", [Seg(w) for w in INSERTED_DECLARATION.split()])
    )
    model.renumber()
    return [
        TruthFlag(
            "AFF-DECL-ADDED",
            "decl:added:after-12",
            INSERTED_DECLARATION,
            None,
            page_key="decl:added",
        )
    ]


def _header_ay_stale(model: PrintModel, draft: Draft, style: Style) -> list[TruthFlag]:
    start = int(draft.header.ay[:4]) - 1
    stale = f"{start}-{str(start + 1)[2:]}"
    model.ay_line = model.ay_line.replace(ay_long(draft.header.ay), ay_long(stale))
    return [TruthFlag("AFF-HEADER", "header:ay", stale, draft.header.ay, page_key="header:ay")]


def _fmt_area(value: float, style: Style) -> str:
    return f"{value:g}" if style.compact_numbers else f"{value:.2f}"


def _land_area_changed(
    row: int | None = None,
) -> Callable[[PrintModel, Draft, Style], list[TruthFlag]]:
    def mutate(model: PrintModel, draft: Draft, style: Style) -> list[TruthFlag]:
        index = (row or len(model.land_rows)) - 1
        key, cells = model.land_rows[index]
        old = draft.land_rows[index].area_acre
        new = round(old - (1.0 if old > 1.5 else 0.5), 2)
        cells[5] = _fmt_area(new, style)
        total = round(sum(r.area_acre for r in draft.land_rows), 2)
        expected_total = round(draft.land_total_acres or 0.0, 2)
        return [
            TruthFlag("LAND-AREA-RECON", f"land:{key}:area_acre", new, old, "acre", f"land:{key}"),
            TruthFlag(
                "LAND-AREA-RECON",
                "land:total",
                round(total - (old - new), 2),
                expected_total,
                "acre",
                "table:land",
            ),
        ]

    return mutate


def _land_row_changed(model: PrintModel, draft: Draft, style: Style) -> list[TruthFlag]:
    key, cells = model.land_rows[0]
    old = cells[3]
    cells[3] = old[:-1] + str((int(old[-1]) + 6) % 10)
    return [
        TruthFlag("LAND-ROW-RECON", f"land:{key}:plot_no", cells[3], old, page_key=f"land:{key}")
    ]


def _room_values_changed(model: PrintModel, draft: Draft, style: Style) -> list[TruthFlag]:
    flags = []
    tables = {t: rows for t, _, rows in model.room_tables}
    instructional = tables["room_instructional"]
    room_id, cells = instructional[1 if len(instructional) > 1 else 0]
    old_area = float(cells[2])
    new_area = old_area - 6.0
    cells[2] = f"{new_area:g}" if style.compact_numbers else f"{new_area:.1f}"
    flags.append(
        TruthFlag(
            "ROOM-RECON",
            f"room_instructional:{room_id}:carpet_area_m2",
            new_area,
            old_area,
            "m2",
            f"room_instructional:{room_id}",
        )
    )
    admin_id, admin_cells = tables["room_admin"][0]
    old_flooring = admin_cells[3]
    admin_cells[3] = "Not ready"
    flags.append(
        TruthFlag(
            "ROOM-RECON",
            f"room_admin:{admin_id}:flooring",
            "Not ready",
            old_flooring,
            None,
            f"room_admin:{admin_id}",
        )
    )
    return flags


def _room_ids_duplicated(snapshot: dict[str, Any]) -> list[TruthFlag]:
    rooms = snapshot["rooms"]
    duplicate = rooms["instructional"][0]["room_id"]
    rooms["instructional_common"][0]["room_id"] = duplicate
    return [
        TruthFlag(
            "ROOM-ID-DUP",
            f"room_id:{duplicate}",
            duplicate,
            None,
            page_key=f"room_common:{duplicate}",
        )
    ]


def plan_for(variant: str, rng: random.Random, demo: bool = False) -> Plan:
    plan = Plan()
    if demo:
        plan.printed += [_cat_line_missing, _clause_narrowed(9), _land_area_changed(2)]
        plan.snapshot.append(_room_ids_duplicated)
        return plan
    match variant:
        case "cat_line_missing":
            plan.printed.append(_cat_line_missing)
        case "decl_dropped":
            plan.printed.append(_decl_dropped(rng.randint(1, 24)))
        case "clause_narrowed":
            plan.printed.append(_clause_narrowed(rng.choice(sorted(NARROWINGS))))
        case "decl_inserted":
            plan.printed.append(_decl_inserted)
        case "header_ay_stale":
            plan.printed.append(_header_ay_stale)
        case "land_area_changed":
            plan.printed.append(_land_area_changed())
        case "land_row_changed":
            plan.printed.append(_land_row_changed)
        case "room_values_changed":
            plan.printed.append(_room_values_changed)
        case "room_ids_duplicated":
            plan.snapshot.append(_room_ids_duplicated)
        case _ if variant in CONTROL_STYLES:
            pass
        case _:
            raise KeyError(f"unknown variant {variant}")
    return plan


def _printed(model: PrintModel) -> dict[str, Any]:
    printed: dict[str, Any] = {f"header.{k}": v for k, _, v in model.header}
    printed["header.ay_line"] = model.ay_line
    printed["categories"] = list(model.categories)
    printed["declarations"] = [d.kept_text() for d in _all_decls(model)]
    for key, cells in model.land_rows:
        printed[f"land.{key}"] = list(cells)
    for table, _, rows in model.room_tables:
        printed[table] = [list(cells) for _, cells in rows]
    return printed


def generate(
    profile: int,
    variant: str,
    ay: str = "2026-27",
    demo: bool = False,
    hooks: Hooks | None = None,
) -> GeneratedCase:
    """One synthetic sworn affidavit + its case, snapshot and ground truth."""
    rng = random.Random(f"satya-m5-{profile}-{variant}-{ay}")
    inst: Institution = institution(profile, ay)
    snapshot, case = inst.snapshot, inst.case
    plan = plan_for(variant, rng, demo)
    truth_flags: list[TruthFlag] = []
    for snap_mutate in plan.snapshot:
        truth_flags += snap_mutate(snapshot)
    if hooks and hooks.case:
        hooks.case(case, snapshot)
    template = load_template(case["affidavit_draft"]["template_id"])
    draft = render_draft(template, draft_header(case, snapshot), case["category_set"], snapshot)
    if variant in CONTROL_STYLES:
        style = CONTROL_STYLES[variant]
    else:
        style = CONTROL_STYLES[rng.choice(sorted(CONTROL_STYLES))]
    model = build_print_model(draft, case, style)
    for print_mutate in plan.printed:
        truth_flags += print_mutate(model, draft, style)
    if hooks and hooks.model:
        hooks.model(model)
    pdf, positions = render(model, style)
    ruleset = load_ruleset()
    expected = []
    for tf in truth_flags:
        rule = ruleset[tf.rule_id]
        expected.append(
            {
                "rule_id": tf.rule_id,
                "check_ref": tf.check_ref,
                "page": positions.get(tf.page_key) if tf.page_key else None,
                "label": rule.label,
                "severity": rule.severity,
                "alert": {"type": rule.alert_type, "subtype": rule.alert_subtype},
                "extracted_value": tf.extracted_value,
                "expected_value": tf.expected_value,
                "value_unit": tf.value_unit,
                "institution_visible": rule.institution_visible,
                "preliminary_indicator": rule.preliminary_indicator,
            }
        )
    name = "demo" if demo else variant
    slug = f"{case['case_id'][-4:].lower()}-{ay}-{name}"
    truth = {
        "_synthetic": case["_synthetic"],
        "case": slug,
        "profile": profile,
        "variant": name,
        "control": variant in CONTROL_STYLES and not demo,
        "style": style.name,
        "slot": "annex2.1(i) affidavit",
        "expected_flags": expected,
        "printed": _printed(model),
    }
    return GeneratedCase(
        slug=slug,
        case=case,
        snapshot=snapshot,
        pdf=pdf,
        truth=truth,
        positions=positions,
        mark_box=model.mark_box,
    )
