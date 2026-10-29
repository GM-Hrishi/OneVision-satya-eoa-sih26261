"""M5 engine: sworn Affidavit 2 + portal draft + ApplicationSnapshot -> AffidavitDiff (UI §6.3).

Deterministic and side-effect free: the same inputs give the same JSON (Portal spec §2.11), so a run
can be replayed. Advisory only; nothing here approves, rejects or clears anything.
"""

from dataclasses import dataclass
from typing import Any

from satya_affidavit.diff import DeclMatch, diff_declarations
from satya_affidavit.extract import Box, Extracted, extract
from satya_affidavit.flags import TEXT_LAYER_CONFIDENCE, FlagFactory, confidence_band
from satya_affidavit.ids import sha256_hex, stable_id
from satya_affidavit.normalise import clean, parse_date, squash, words_of
from satya_affidavit.parse import SwornDoc, parse
from satya_affidavit.reconcile import Reconciled, reconcile
from satya_affidavit.rules import Ruleset, load_ruleset
from satya_affidavit.template import (
    CORE_COUNT,
    EXISTING_COUNT,
    Draft,
    draft_header,
    load_template,
    render_draft,
)
from satya_ocr.model import OcrLayer

ENGINE_VERSION = "0.1.0"
DRAFT_LABEL = "Portal affidavit draft for this AID and AY"
HEADER_CHECKS = ("ay", "aid", "pid", "institution_name", "application_date")
PENDING = [
    {"section": "stamp", "module": "M6", "promise": "P-4"},
    {"section": "chronology", "module": "M6", "promise": "P-4"},
    {"section": "signatures", "module": "M6", "promise": "P-4"},
]


OCR_PENDING = [{"section": "ocr", "module": "M3", "promise": "P-2"}]


def _ocr_mean(extracted: Any) -> float | None:
    if not extracted.ocr_pages:
        return None
    return float(round(sum(extracted.ocr_pages.values()) / len(extracted.ocr_pages), 3))


def _ocr_flag(flag: dict[str, Any], ocr_pages: dict[int, float]) -> dict[str, Any]:
    """A finding that rests on OCR text: advisory, preliminary, never above manual review.

    A flag with no page (header fields) is read from the first OCR-affected page's confidence."""
    page = flag.get("page")
    confidence = ocr_pages.get(page) if page is not None else None
    if confidence is None:
        if page is not None and page not in ocr_pages:
            return flag  # the finding rests on the native text layer of another page
        confidence = min(ocr_pages.values())
    source = dict(flag["extracted_source"])
    source["doc_label"] = f"{source['doc_label']}, read by OCR ({round(confidence * 100)}%)"
    return {
        **flag,
        "extracted_source": source,
        "confidence": round(min(flag["confidence"], confidence), 3),
        "confidence_band": confidence_band(min(flag["confidence"], confidence)),
        "preliminary_indicator": True,
        "label": "manual_review_required",
    }


@dataclass(frozen=True)
class CaseInput:
    """One case as the gateway holds it: case metadata (incl. affidavit_draft), snapshot, PDF."""

    case: dict[str, Any]
    snapshot: dict[str, Any]
    pdf: bytes
    token_key: bytes
    ocr: dict[int, OcrLayer] | None = None  # OCR text layers of image-only pages (satya_ocr)
    unreadable_pages: int | None = None  # set when satya_ocr blocked the file: nothing is extracted
    ruleset: Ruleset | None = None  # replay (P-11): an archived rule pack; default = current


@dataclass
class EngineResult:
    diff: dict[str, Any]
    sworn: SwornDoc | None
    draft: Draft


def _region(doc: SwornDoc, page: int | None, box: Box | None) -> list[dict[str, float]]:
    if page is None or box is None or page not in doc.pages:
        return []
    return [doc.pages[page].region(box)]


def _category_state(expected: list[str], found: list[str]) -> str:
    exp = {squash(c).rstrip(".") for c in expected}
    got = {squash(c).rstrip(".") for c in found}
    if not got:
        return "missing"
    if got == exp:
        return "present"
    if exp < got:
        return "extra"
    return "different"


def _header_flags(doc: SwornDoc, draft: Draft, factory: FlagFactory) -> list[dict[str, Any]]:
    flags = []
    order = draft.template.date_order
    for key in HEADER_CHECKS:
        if key == "ay":
            got: Any = doc.ay
            want: Any = draft.header.ay
            same = got == want
            page, box = doc.heading_page, None
        else:
            located = doc.header.get(key)
            got = located.text if located else None
            page, box = (located.page, located.box) if located else (doc.heading_page, None)
            if key == "application_date":
                parsed, _ = parse_date(got, order)
                want = draft.header_value(key)
                same = parsed == draft.header.application_date
            else:
                want = draft.header_value(key)
                same = got is not None and squash(got) == squash(want)
        if same:
            continue
        flags.append(
            factory.make(
                "AFF-HEADER",
                f"header:{key}",
                page=page,
                regions=_region(doc, page, box),
                extracted=got,
                expected=want,
                row=key,
                expected_label=f"{DRAFT_LABEL}: header.{key}",
                confidence=TEXT_LAYER_CONFIDENCE if got is not None else 0.9,
            )
        )
    return flags


def _decl_flags(
    matches: list[DeclMatch], doc: SwornDoc, factory: FlagFactory
) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    previous_expected = 0
    previous_sworn = None
    for m in matches:
        if m.op == "equal":
            previous_expected = m.expected.no if m.expected else previous_expected
            previous_sworn = m.sworn
            continue
        if m.op == "removed" and m.expected:
            anchor = previous_sworn
            page = anchor.page if anchor else doc.heading_page
            flag = factory.make(
                "AFF-DECL-MISSING",
                f"decl:{m.expected.no}",
                page=page,
                regions=_region(doc, page, anchor.box if anchor else None),
                extracted=None,
                expected=m.expected.display,
                row=str(m.expected.no),
                expected_label=f"{DRAFT_LABEL}: declaration {m.expected.no}",
                confidence=0.95,
            )
            previous_expected = m.expected.no
        elif m.op == "changed" and m.expected and m.sworn:
            flag = factory.make(
                "AFF-DECL-CHANGED",
                f"decl:{m.expected.no}",
                page=m.sworn.page,
                regions=_region(doc, m.sworn.page, m.sworn.box),
                extracted=m.sworn.text,
                expected=m.expected_view,
                row=str(m.expected.no),
                expected_label=f"{DRAFT_LABEL}: declaration {m.expected.no}",
                confidence=0.95 if m.similarity >= 0.75 else 0.8,
            )
            previous_expected = m.expected.no
            previous_sworn = m.sworn
        elif m.op == "added" and m.sworn:
            flag = factory.make(
                "AFF-DECL-ADDED",
                f"decl:added:after-{previous_expected}",
                page=m.sworn.page,
                regions=_region(doc, m.sworn.page, m.sworn.box),
                extracted=m.sworn.text,
                expected=None,
                row=str(m.sworn.position),
                expected_label=f"{DRAFT_LABEL}: no such declaration",
                confidence=0.95,
            )
            previous_sworn = m.sworn
        else:
            continue
        m.flag_id = flag["flag_id"]
        flags.append(flag)
    return flags


def run(inp: CaseInput) -> EngineResult:
    case, snapshot = inp.case, inp.snapshot
    draft_meta = case["affidavit_draft"]
    template = load_template(draft_meta["template_id"])
    draft = render_draft(
        template, draft_header(case, snapshot), list(draft_meta["category_set"]), snapshot
    )
    ruleset = inp.ruleset or load_ruleset()
    sha = sha256_hex(inp.pdf)
    doc_id = stable_id("doc", sha)
    factory = FlagFactory(ruleset, doc_id, sha)
    extracted = Extracted([], 0) if inp.unreadable_pages is not None else extract(inp.pdf, inp.ocr)
    vocabulary: set[str] = set()
    for decl in draft.declarations:
        vocabulary |= set(words_of(decl.display))
    vocabulary |= set(words_of(" ".join(draft.entities().values())))

    expected_block = {
        "template_id": template.template_id,
        "template_year": template.aph_edition,
        "aid": draft.header.aid,
        "category_list": list(draft.category_list),
        "declarations": [
            {"no": d.no, "printed_no": d.printed_no, "block": d.block, "text": d.display}
            for d in draft.declarations
        ],
    }
    base_case = {
        "case_id": case["case_id"],
        "application_id": case["application_id"],
        "permanent_id": case.get("permanent_id"),
        "ay": case["ay"],
        "regional_office": case["regional_office"],
        "institution_name": case.get("institution_name"),
        "route": case["route"],
        "stage": case["stage"],
        "category_set": list(case["category_set"]),
    }
    base_case = {k: v for k, v in base_case.items() if v is not None}

    if extracted.text_layer_pages == 0:
        diff = _empty(
            base_case,
            doc_id,
            sha,
            ruleset.ref,
            expected_block,
            inp.unreadable_pages if inp.unreadable_pages is not None else extracted.page_count,
            template.date_order,
        )
        return EngineResult(diff, None, draft)

    doc = parse(extracted, template, vocabulary)
    entities = draft.entities()
    matches = diff_declarations(draft.declarations, doc.declarations, entities)
    flags: list[dict[str, Any]] = []

    found = [c.text for c in doc.categories]
    state = _category_state(list(draft.category_list), found)
    cat_page = doc.category_label.page if doc.category_label else doc.heading_page
    cat_box = doc.category_label.box if doc.category_label else None
    category_line: dict[str, Any] = {
        "expected": list(draft.category_list),
        "found": found,
        "state": state,
        "page": cat_page,
    }
    if state != "present":
        flag = factory.make(
            "AFF-CAT-LINE",
            "category_line",
            page=cat_page,
            regions=_region(doc, cat_page, cat_box),
            extracted="; ".join(found) or None,
            expected="; ".join(draft.category_list),
            row="category_line",
            expected_label=f"{DRAFT_LABEL}: category list",
            confidence=TEXT_LAYER_CONFIDENCE if doc.category_label else 0.9,
        )
        category_line["flag_id"] = flag["flag_id"]
        flags.append(flag)
    flags += _header_flags(doc, draft, factory)
    flags += _decl_flags(matches, doc, factory)
    # Tables need ruled-line geometry that a scan does not give; they are not read from OCR pages.
    tables = Reconciled() if extracted.ocr_pages else reconcile(doc, draft, factory, inp.token_key)
    flags += tables.flags
    if extracted.ocr_pages:
        flags = [_ocr_flag(f, extracted.ocr_pages) for f in flags]

    template_match = doc.heading == template.heading and doc.ay in template.valid_ays
    options = []
    for m in matches:
        if m.expected and m.sworn:
            for group in m.expected.groups:
                options.append(
                    {
                        "decl_no": m.expected.no,
                        "group": group.name,
                        "choices": list(group.choices),
                        "selected": m.selected.get(group.name, []),
                    }
                )
    ops = []
    for m in matches:
        op: dict[str, Any] = {
            "op": m.op,
            "decl_no": m.expected.no if m.expected else None,
            "sworn_no": m.sworn.position if m.sworn else None,
            "similarity": m.similarity,
            "spans": [{"kind": s.kind, "text": s.text} for s in m.spans],
        }
        if m.flag_id:
            op["flag_id"] = m.flag_id
        ops.append(op)
    diff = {
        "case": base_case,
        "doc_id": doc_id,
        "run_id": stable_id("run", sha, ruleset.ref, template.template_id, ENGINE_VERSION),
        "engine_version": ENGINE_VERSION,
        "ruleset_version": ruleset.ref,
        "advisory": True,
        "expected": expected_block,
        "sworn": {
            "page_count": extracted.page_count,
            "sha256": sha,
            "template_match": template_match,
            "template_detected": template.template_id if template_match else None,
            "text_source": "ocr" if extracted.ocr_pages else "text_layer",
            "ocr_mean_confidence": _ocr_mean(extracted),
            "issuer_sig": None,
            "uploader_sig": None,
            "category_list_found": found or None,
            "declarations": [
                {
                    "no": d.position,
                    "printed_no": d.printed_no,
                    "block": d.block,
                    "text": clean(d.text) or "(empty)",
                    "page": d.page,
                    "region": doc.pages[d.page].region(d.box),
                    "ocr_confidence": extracted.ocr_pages.get(d.page),
                }
                for d in doc.declarations
            ],
        },
        "normalisation": {
            "whitespace": True,
            "strike_through_resolved": doc.struck_words,
            "names_substituted": True,
            "hyphens_rejoined": doc.hyphens_rejoined,
            "date_order": template.date_order,
            "date_order_fallbacks": tables.date_fallbacks,
        },
        "options": options,
        "ops": ops,
        "structure": {
            "category_line": category_line,
            "core": {
                "expected": CORE_COUNT,
                "found": sum(1 for d in doc.declarations if d.block == "core"),
            },
            "existing_institute": {
                "expected": EXISTING_COUNT,
                "found": sum(1 for d in doc.declarations if d.block == "existing_institute"),
            },
            "extra_blocks": [{"heading": b.text, "page": b.page} for b in doc.extra_blocks],
        },
        "tables": tables.tables,
        "stamp": None,
        "chronology": None,
        "pending": [*PENDING, *OCR_PENDING] if extracted.ocr_pages else PENDING,
        "flags": flags,
    }
    return EngineResult(diff, doc, draft)


def _empty(
    base_case: dict[str, Any],
    doc_id: str,
    sha: str,
    ruleset_ref: str,
    expected_block: dict[str, Any],
    page_count: int,
    date_order: str,
) -> dict[str, Any]:
    """No text layer: nothing can be compared until OCR (M3, P-2); no flag is raised."""
    return {
        "case": base_case,
        "doc_id": doc_id,
        "engine_version": ENGINE_VERSION,
        "ruleset_version": ruleset_ref,
        "advisory": True,
        "expected": expected_block,
        "sworn": {
            "page_count": page_count,
            "sha256": sha,
            "template_match": False,
            "template_detected": None,
            "text_source": "text_layer",
            "ocr_mean_confidence": None,
            "issuer_sig": None,
            "uploader_sig": None,
            "category_list_found": None,
            "declarations": [],
        },
        "normalisation": {
            "whitespace": True,
            "strike_through_resolved": 0,
            "names_substituted": True,
            "hyphens_rejoined": 0,
            "date_order": date_order,
            "date_order_fallbacks": 0,
        },
        "options": [],
        "ops": [],
        "structure": {
            "category_line": {
                "expected": expected_block["category_list"],
                "found": [],
                "state": "missing",
            },
            "core": {"expected": CORE_COUNT, "found": 0},
            "existing_institute": {"expected": EXISTING_COUNT, "found": 0},
            "extra_blocks": [],
        },
        "tables": [],
        "stamp": None,
        "chronology": None,
        "pending": [*PENDING, {"section": "ocr", "module": "M3", "promise": "P-2"}],
        "flags": [],
    }
