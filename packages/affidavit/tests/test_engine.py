"""M5 engine + reconciliation (S1.6): flags, schema, determinism, masking, edge cases."""

import copy
import io
import json
from typing import Any

from reportlab.pdfgen.canvas import Canvas

from satya_affidavit.engine import CaseInput, run
from satya_affidavit.ids import token
from satya_affidavit.synth.render import PrintDecl, Seg, build_print_model, render
from satya_affidavit.synth.variants import CONTROL_STYLES, generate
from satya_affidavit.template import draft_header, load_template, render_draft
from satya_shared_types import validator

KEY = b"test-token-key-synthetic-only-000000001"


def _run(
    case: Any, snapshot: dict[str, Any] | None = None, pdf: bytes | None = None
) -> dict[str, Any]:
    result = run(CaseInput(case.case, snapshot or case.snapshot, pdf or case.pdf, KEY))
    return result.diff


def test_demo_case_flags_match_the_planted_truth() -> None:
    case = generate(3, "clean", demo=True)
    diff = _run(case)
    assert sorted(f["check_ref"] for f in diff["flags"]) == sorted(
        f["check_ref"] for f in case.truth["expected_flags"]
    )
    assert diff["structure"]["category_line"]["state"] == "missing"
    land = next(t for t in diff["tables"] if t["table"] == "land")
    assert land["computed_total_acres"] == 11.5 and land["expected_total_acres"] == 12.5
    common = next(t for t in diff["tables"] if t["table"] == "room_common")
    assert common["room_id_duplicates"] == ["I-201"]


def test_output_is_a_valid_affidavit_diff_and_every_flag_is_cited() -> None:
    diff = _run(generate(3, "clean", demo=True))
    assert [e.message for e in validator("AffidavitDiff").iter_errors(diff)] == []
    assert diff["advisory"] is True
    for flag in diff["flags"]:
        assert flag["aph_clause"] and flag["aph_edition"] == "2024-27" and flag["rule_version"]
        assert flag["page"] and flag["regions"], flag["check_ref"]
        assert flag["disposition"] is None and flag["provenance"] == "satya"
        assert flag["preliminary_indicator"] is True


def test_flags_are_linked_from_ops_and_rows() -> None:
    diff = _run(generate(3, "clean", demo=True))
    ids = {f["flag_id"] for f in diff["flags"]}
    linked = {op["flag_id"] for op in diff["ops"] if "flag_id" in op}
    linked |= {fid for t in diff["tables"] for r in t["rows"] for fid in r["flag_ids"]}
    linked |= {diff["structure"]["category_line"]["flag_id"]}
    # The land total has no row of its own; the DiffView shows it beside the computed total.
    total_ref = "m5:LAND-AREA-RECON:land:total"
    total = {f["flag_id"] for f in diff["flags"] if f["check_ref"] == total_ref}
    assert linked | total == ids


def test_runs_are_deterministic() -> None:
    case = generate(9, "room_values_changed")
    assert json.dumps(_run(case), sort_keys=True) == json.dumps(_run(case), sort_keys=True)


def test_tokenised_identifiers_never_appear_in_the_output() -> None:
    case = generate(3, "clean")
    text = json.dumps(_run(case))
    for deed in case.snapshot["land"]["deeds"]:
        assert deed["document_no"] not in text
    tables = json.dumps(_run(case)["tables"])
    assert case.snapshot["trust"]["name"] not in tables


def test_pre_tokenised_snapshot_deeds_reconcile() -> None:
    case = generate(5, "clean")
    snapshot = copy.deepcopy(case.snapshot)
    for deed in snapshot["land"]["deeds"]:
        deed["deed_token"] = token(KEY, deed.pop("document_no"), identifier=True)
    diff = _run(case, snapshot=snapshot)
    assert diff["flags"] == []


def test_clean_controls_raise_no_flags() -> None:
    for variant in CONTROL_STYLES:
        assert _run(generate(13, variant))["flags"] == [], variant


def test_a_scan_without_text_layer_raises_nothing_and_waits_for_ocr() -> None:
    buf = io.BytesIO()
    canvas = Canvas(buf, invariant=True)
    canvas.rect(50, 50, 200, 200)
    canvas.showPage()
    canvas.save()
    diff = _run(generate(3, "clean"), pdf=buf.getvalue())
    assert diff["flags"] == []
    assert {"section": "ocr", "module": "M3", "promise": "P-2"} in diff["pending"]
    assert [e.message for e in validator("AffidavitDiff").iter_errors(diff)] == []


def test_an_extra_block_is_reported_and_its_declarations_flagged() -> None:
    case = generate(7, "clean")
    template = load_template("aff2-portal-2024-27")
    draft = render_draft(
        template, draft_header(case.case, case.snapshot), ["EoA Only"], case.snapshot
    )
    style = CONTROL_STYLES["clean"]
    model = build_print_model(draft, case.case, style)
    sentence = "The intake applied for is supported by the additional built-up area."
    words = sentence.split(" ")
    model.extra_blocks = [
        ("FOR INCREASE IN INTAKE", [PrintDecl("decl:added", 1, "extra", [Seg(w) for w in words])])
    ]
    pdf, _ = render(model, style)
    diff = _run(case, pdf=pdf)
    assert [b["heading"] for b in diff["structure"]["extra_blocks"]] == ["FOR INCREASE IN INTAKE"]
    assert [f["check_ref"] for f in diff["flags"]] == ["m5:AFF-DECL-ADDED:decl:added:after-24"]
    assert diff["sworn"]["declarations"][-1]["block"] == "extra"
