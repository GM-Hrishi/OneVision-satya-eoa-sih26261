"""Template profile, expected draft and ruleset (S1.2)."""

import re
from typing import Any

from satya_affidavit.rules import load_ruleset
from satya_affidavit.template import draft_header, load_template, render_draft

TEMPLATE = "aff2-portal-2024-27"


def test_template_has_19_core_and_5_existing_declarations() -> None:
    template = load_template(TEMPLATE)
    blocks = [d["block"] for d in template.declarations]
    assert blocks.count("core") == 19
    assert blocks.count("existing_institute") == 5
    assert template.date_order == "MM/DD/YYYY"
    assert set(template.valid_ays) == {"2024-25", "2025-26", "2026-27"}


def test_draft_numbers_restart_in_the_existing_institute_block(
    example_case: dict[str, Any], example_snapshot: dict[str, Any]
) -> None:
    template = load_template(TEMPLATE)
    draft = render_draft(
        template, draft_header(example_case, example_snapshot), ["EoA Only"], example_snapshot
    )
    assert [d.no for d in draft.declarations] == list(range(1, 25))
    assert draft.declarations[19].printed_no == 1
    assert draft.declarations[19].block == "existing_institute"
    assert draft.ay_line == "ACADEMIC YEAR – 2026-2027"


def test_option_groups_print_as_choices_and_compare_as_tokens(
    example_case: dict[str, Any], example_snapshot: dict[str, Any]
) -> None:
    template = load_template(TEMPLATE)
    draft = render_draft(
        template, draft_header(example_case, example_snapshot), ["EoA Only"], example_snapshot
    )
    decl9 = draft.declarations[8]
    assert "owned / leased" in decl9.display
    assert "<opt:land_tenure>" in decl9.tokenised
    assert [g.name for g in decl9.groups] == ["land_tenure", "entity"]


def test_draft_tables_come_from_the_snapshot(
    example_case: dict[str, Any], example_snapshot: dict[str, Any]
) -> None:
    template = load_template(TEMPLATE)
    draft = render_draft(
        template, draft_header(example_case, example_snapshot), ["EoA Only"], example_snapshot
    )
    assert [r.area_acre for r in draft.land_rows] == [8.0, 4.5]
    assert draft.land_total_acres == 12.5


def test_every_rule_cites_a_clause_and_edition() -> None:
    ruleset = load_ruleset()
    assert ruleset.ref == "m5-affidavit@0.1.0"
    assert len(ruleset.rules) == 9
    for rule in ruleset.rules.values():
        assert re.fullmatch(r"[A-Z][A-Z0-9-]{1,63}", rule.rule_id)
        assert rule.aph_clause and rule.aph_edition == "2024-27"
        assert rule.severity in {"info", "warning", "critical"}
        assert rule.label in {"mismatch_detected", "manual_review_required"}
        assert rule.preliminary_indicator is True
