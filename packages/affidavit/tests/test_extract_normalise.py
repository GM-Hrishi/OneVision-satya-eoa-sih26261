"""Text extraction and normalisation (S1.4): strike-through, hyphen re-join, tables, MM/DD dates."""

from datetime import date

import pytest

from satya_affidavit.extract import ExtractionError, extract
from satya_affidavit.normalise import (
    OptionGroup,
    canonical,
    clean,
    join_wrapped,
    parse_date,
    parse_number,
    resolve_options,
    squash,
)
from satya_affidavit.parse import SwornDoc, parse
from satya_affidavit.synth.variants import generate
from satya_affidavit.template import draft_header, load_template, render_draft


def _parsed(profile: int, variant: str) -> SwornDoc:
    case = generate(profile, variant)
    template = load_template("aff2-portal-2024-27")
    draft = render_draft(
        template, draft_header(case.case, case.snapshot), ["EoA Only"], case.snapshot
    )
    vocabulary = {w.casefold().strip(".,;:") for d in draft.declarations for w in d.display.split()}
    return parse(extract(case.pdf), template, vocabulary)


def test_struck_choices_are_dropped_from_the_text_layer() -> None:
    doc = _parsed(3, "clean")
    decl9 = doc.declarations[8].text
    assert "owned by the Trust" in decl9
    assert "leased" not in decl9 and "Society" not in decl9
    assert doc.struck_words >= 6


def test_alternative_choices_survive() -> None:
    doc = _parsed(3, "clean_alt_options")
    assert "leased by the Company" in doc.declarations[8].text


def test_hyphen_wrapped_words_are_rejoined() -> None:
    doc = _parsed(3, "clean_hyphenated")
    assert doc.hyphens_rejoined > 0
    joined = " ".join(d.text for d in doc.declarations)
    assert "-\n" not in joined
    assert "approved location" in joined


def test_tables_read_cell_by_cell_with_repeated_headers_skipped() -> None:
    doc = _parsed(3, "clean")
    assert [r.cells[1] for r in doc.tables["land"].rows] == ["DEMO-DEED-0301", "DEMO-DEED-0302"]
    assert doc.tables["room_instructional"].rows[0].cells[:3] == ["I-201", "Class Room", "66.0"]
    assert all(r.cells[0] != "Room No." for t in doc.tables.values() for r in t.rows)


def test_opening_block_and_blocks() -> None:
    doc = _parsed(5, "clean")
    assert doc.heading == "AFFIDAVIT" and doc.ay == "2026-27"
    assert doc.header["aid"].text == "1-90000005105"
    assert [c.text for c in doc.categories] == ["EoA Only"]
    blocks = [d.block for d in doc.declarations]
    assert blocks.count("core") == 19 and blocks.count("existing_institute") == 5
    assert doc.declarations[19].printed_no == 1


def test_unreadable_bytes_raise() -> None:
    with pytest.raises(ExtractionError):
        extract(b"not a pdf")


@pytest.mark.parametrize(
    ("text", "expected", "fallback"),
    [
        ("06/15/2009", date(2009, 6, 15), False),
        ("15/06/2009", date(2009, 6, 15), True),  # impossible month in MM/DD: parsed the other way
        ("02/03/2012", date(2012, 2, 3), False),
        ("2012-02-20", date(2012, 2, 20), False),
        ("31/31/2012", None, False),
        ("", None, False),
    ],
)
def test_portal_dates_are_mm_dd(text: str, expected: date | None, fallback: bool) -> None:
    assert parse_date(text, "MM/DD/YYYY") == (expected, fallback)


def test_numbers_whitespace_and_dashes() -> None:
    assert parse_number("8") == parse_number("8.00") == 8.0
    assert parse_number("1,250.5") == 1250.5
    assert parse_number("n/a") is None
    assert clean("ACADEMIC  YEAR – 2026") == "ACADEMIC YEAR - 2026"
    assert squash("Demo  Institute\nof Technology") == squash("demo institute of technology")


def test_hyphen_rejoin_keeps_real_compounds() -> None:
    vocabulary = {"self-financing", "accordance"}
    assert join_wrapped("Private Self-", "Financing", vocabulary) == (
        "Private Self-Financing",
        False,
    )
    assert join_wrapped("in accor-", "dance with", vocabulary) == ("in accordance with", True)
    assert join_wrapped("plain", "text", vocabulary) == ("plain text", False)


def test_option_groups_resolve_to_tokens() -> None:
    group = OptionGroup("land_tenure", ("owned", "leased"))
    assert resolve_options("is owned by", [group]) == (
        "is <opt:land_tenure> by",
        {"land_tenure": ["owned"]},
    )
    text, selected = resolve_options("is owned / leased by", [group])
    assert text == "is <opt:land_tenure> by" and selected == {"land_tenure": ["owned", "leased"]}


def test_names_are_substituted_ignoring_case() -> None:
    entities = {"institution_name": "Demo Institute of Technology 03"}
    a, _ = canonical("runs DEMO INSTITUTE OF  TECHNOLOGY 03.", entities)
    b, _ = canonical("runs Demo Institute of Technology 03.", entities)
    assert a == b == "runs <institution_name>."
