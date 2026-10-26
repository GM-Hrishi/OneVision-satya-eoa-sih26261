"""Clause-level diff (S1.5): content alignment, renumbering, options, word spans."""

from satya_affidavit.diff import diff_declarations, word_spans
from satya_affidavit.extract import extract
from satya_affidavit.normalise import words_of
from satya_affidavit.parse import parse
from satya_affidavit.synth.variants import generate
from satya_affidavit.template import draft_header, load_template, render_draft


def _ops(profile: int, variant: str) -> list[tuple[str, int | None]]:
    case = generate(profile, variant)
    template = load_template("aff2-portal-2024-27")
    draft = render_draft(
        template, draft_header(case.case, case.snapshot), ["EoA Only"], case.snapshot
    )
    vocabulary = {w for d in draft.declarations for w in words_of(d.display)}
    doc = parse(extract(case.pdf), template, vocabulary)
    matches = diff_declarations(draft.declarations, doc.declarations, draft.entities())
    return [(m.op, m.expected.no if m.expected else None) for m in matches if m.op != "equal"]


def test_clean_controls_have_no_differences() -> None:
    for variant in ("clean", "clean_hyphenated", "clean_alt_options", "clean_spacing_case"):
        assert _ops(7, variant) == [], variant


def test_dropped_declaration_is_one_removal_despite_renumbering() -> None:
    ops = _ops(11, "decl_dropped")
    assert len(ops) == 1 and ops[0][0] == "removed"


def test_narrowed_clause_is_a_change_of_that_declaration() -> None:
    case = generate(3, "clean", demo=True)
    template = load_template("aff2-portal-2024-27")
    draft = render_draft(
        template, draft_header(case.case, case.snapshot), ["EoA Only"], case.snapshot
    )
    vocabulary = {w for d in draft.declarations for w in words_of(d.display)}
    doc = parse(extract(case.pdf), template, vocabulary)
    changed = [
        m
        for m in diff_declarations(draft.declarations, doc.declarations, draft.entities())
        if m.op != "equal"
    ]
    assert [(m.op, m.expected.no if m.expected else None) for m in changed] == [("changed", 9)]
    deleted = [s.text for s in changed[0].spans if s.kind == "delete"]
    assert deleted == ["contiguous and undisputed,"]
    assert changed[0].selected == {"land_tenure": ["owned"], "entity": ["Trust"]}


def test_inserted_declaration_is_an_addition() -> None:
    assert _ops(5, "decl_inserted") == [("added", None)]


def test_word_spans_mark_deletions_and_insertions() -> None:
    spans = word_spans("land is contiguous and undisputed", "land is contiguous")
    assert [(s.kind, s.text) for s in spans] == [
        ("equal", "land is contiguous"),
        ("delete", "and undisputed"),
    ]
    spans = word_spans("a b", "a x b")
    assert [(s.kind, s.text) for s in spans] == [("equal", "a"), ("insert", "x"), ("equal", "b")]


def test_case_only_differences_are_equal_spans() -> None:
    spans = word_spans("Demo Institute", "DEMO INSTITUTE")
    assert [s.kind for s in spans] == ["equal"]
