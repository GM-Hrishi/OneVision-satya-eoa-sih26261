"""B-28: scans and unreadable files never crash the gateway and never become `verified`.

Scans are made by rasterising our own synthetic PDFs; the OCR engine is the FakeOcrEngine, which
returns the words of the source PDF. The real PaddleOCR engine is not exercised here.
"""

import io
from collections.abc import Callable, Iterator
from pathlib import Path

import pikepdf
import pytest
from fastapi.testclient import TestClient

from satya_api.auth import TokenVerifier
from satya_api.cases import FixtureCaseRepository
from satya_api.config import Settings
from satya_api.main import create_app
from satya_api.store import MemoryStore
from satya_forensics.registry import Registry
from satya_ocr import FakeOcrEngine, OcrSettings
from satya_ocr.synth import rasterise
from satya_ocr.testing import fake_from_source_pdf

from .test_workbench_api import CASES, DCE05, ISSUER, TOKEN_KEY, _jwks, _ok, auth, token

AFFIDAVIT = (CASES / "dce05-2026-27" / "affidavit-sworn.pdf").read_bytes()
URL = f"/v1/cases/{DCE05}/documents?slot=affidavit&filename=scan.pdf"
HEADERS = {**auth(token()), "Content-Type": "application/pdf"}

Factory = Callable[..., TestClient]


@pytest.fixture
def make_client(tmp_path: Path) -> Iterator[Factory]:
    clients: list[TestClient] = []

    async def fetch() -> dict:  # type: ignore[type-arg]
        return _jwks()

    def build(engine: FakeOcrEngine | None, ocr: OcrSettings | None = None) -> TestClient:
        settings = Settings(
            env="test",
            rate_limit="1000/minute",
            user_rate_limit="1000/minute",
            upload_dir=str(tmp_path / f"u{len(clients)}"),
            upload_rate_limit="1000/minute",
            ocr_rate_limit="1000/minute",
        )
        # The five original cases only: one fake engine returns one document's text for every
        # scan, so the three seeded scan cases would register that text as their own.
        root = tmp_path / f"cases{len(clients)}"
        root.mkdir()
        for case_dir in CASES.iterdir():
            if case_dir.name[:5] in ("dit03", "dce05", "dit11", "dce07", "dce09"):
                (root / case_dir.name).symlink_to(case_dir)
        repo = FixtureCaseRepository(
            root,
            TOKEN_KEY,
            ocr_engine=engine,
            ocr_settings=ocr,
            pki_dir=CASES.parent / "pki",
            registry_file=CASES.parent / "registry" / "prior-filings.json",
        )
        app = create_app(
            settings,
            store=MemoryStore(),
            checks={"postgres": _ok, "valkey": _ok, "keycloak": _ok},
            cases=repo,
            verifier=TokenVerifier(ISSUER, "satya-web", fetch),
        )
        client = TestClient(app)
        client.__enter__()
        clients.append(client)
        return client

    yield build
    for client in clients:
        client.__exit__(None, None, None)


def affidavit_doc(view: dict) -> dict:  # type: ignore[type-arg]
    return next(d for d in view["documents"] if d["slot"] == "annex2.1(i) affidavit")


def entries(client: TestClient) -> list[dict]:  # type: ignore[type-arg]
    return client.get(f"/v1/audit?case_id={DCE05}", headers=auth(token())).json()["entries"]


def manual_tasks(client: TestClient) -> int:
    body = client.get("/v1/overview?ay=2026-27", headers=auth(token())).json()
    return int(body["manual_tasks"]["open"])


def test_clean_scan_is_read_by_ocr_and_still_manual_review(make_client: Factory) -> None:
    scan = rasterise(AFFIDAVIT, dpi=150, skew_deg=0.4, seed=3)
    client = make_client(fake_from_source_pdf(AFFIDAVIT, 0.93))
    before = manual_tasks(client)
    r = client.post(URL, content=scan, headers=HEADERS)
    assert r.status_code == 201, r.text
    doc = affidavit_doc(r.json())
    assert doc["label"] == "manual_review_required"
    assert doc["read"]["status"] == "ocr_read" and doc["read"]["reason_code"] == "SCAN_IMAGE_ONLY"
    assert doc["read"]["ocr_mean_confidence"] == 0.93
    assert all(p["kind"] == "image_only" for p in doc["read"]["pages"])
    assert "read by OCR (confidence 93%)" in doc["read"]["why"]
    # M5 ran on the OCR text and says so
    diff = client.get(f"/v1/cases/{DCE05}/affidavit-diff", headers=auth(token())).json()
    assert diff["sworn"]["text_source"] == "ocr" and diff["sworn"]["ocr_mean_confidence"] == 0.93
    assert len(diff["sworn"]["declarations"]) > 5
    assert {d["ocr_confidence"] for d in diff["sworn"]["declarations"]} == {0.93}
    # ledger entry and manual task; the band does not rise because of the scan
    types = [e["event_type"] for e in entries(client)]
    assert "document.read" in types and "manual_task.created" in types
    assert manual_tasks(client) == before + 1
    assert r.json()["risk"]["band"] == "low"


def test_ocr_findings_are_advisory_and_never_above_manual_review(make_client: Factory) -> None:
    # a different sworn affidavit in the same slot: M5 will find differences when read by OCR
    other = (CASES / "dit03-2026-27" / "affidavit-sworn.pdf").read_bytes()
    client = make_client(fake_from_source_pdf(other, 0.9))
    r = client.post(URL, content=rasterise(other, dpi=150, seed=5), headers=HEADERS)
    assert r.status_code == 201
    flags = [f for f in r.json()["flags"] if f["rule_id"].startswith("AFF-")]
    assert flags, "the flagship affidavit has planted M5 findings"
    for f in flags:
        assert f["label"] == "manual_review_required" and f["preliminary_indicator"] is True
        assert "read by OCR" in f["extracted_source"]["doc_label"]
        assert f["confidence"] <= 0.9


def test_low_confidence_scan_falls_back(make_client: Factory) -> None:
    scan = rasterise(AFFIDAVIT, dpi=70, skew_deg=2.0, noise=0.05, blur=1.2, seed=9)
    client = make_client(fake_from_source_pdf(AFFIDAVIT, 0.52))
    r = client.post(URL, content=scan, headers=HEADERS)
    assert r.status_code == 201
    doc = affidavit_doc(r.json())
    assert doc["label"] == "manual_review_required"
    assert doc["read"]["reason_code"] == "OCR_LOW_CONFIDENCE" and "52%" in doc["read"]["why"]
    diff = client.get(f"/v1/cases/{DCE05}/affidavit-diff", headers=auth(token())).json()
    assert diff["flags"] == [] and diff["sworn"]["declarations"] == []
    assert r.json()["risk"]["band"] == "low"


def test_scan_without_an_engine_is_ocr_unavailable(make_client: Factory) -> None:
    client = make_client(None)
    r = client.post(URL, content=rasterise(AFFIDAVIT, dpi=100), headers=HEADERS)
    assert r.status_code == 201
    doc = affidavit_doc(r.json())
    assert doc["read"]["reason_code"] == "OCR_UNAVAILABLE" and doc["label"] != "verified"


def test_ocr_timeout_falls_back_without_an_error(make_client: Factory) -> None:
    engine = FakeOcrEngine([[]], delay_s=0.5)
    client = make_client(engine, OcrSettings(page_timeout_s=0.05))
    r = client.post(URL, content=rasterise(AFFIDAVIT, dpi=100), headers=HEADERS)
    assert r.status_code == 201
    assert affidavit_doc(r.json())["read"]["variant"] == "scan_timeout"


def _encrypted() -> bytes:
    buf = io.BytesIO()
    with pikepdf.open(io.BytesIO(AFFIDAVIT)) as pdf:
        pdf.save(buf, encryption=pikepdf.Encryption(user="pw", owner="ow"))
    return buf.getvalue()


def _zero_pages() -> bytes:
    buf = io.BytesIO()
    pikepdf.new().save(buf)
    return buf.getvalue()


def _blank() -> bytes:
    pdf = pikepdf.new()
    for _ in range(3):
        pdf.add_blank_page(page_size=(595, 842))
    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


def _many_pages() -> bytes:
    pdf = pikepdf.new()
    for _ in range(60):
        pdf.add_blank_page(page_size=(200, 200))
    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


@pytest.mark.parametrize(
    ("name", "data", "variant"),
    [
        ("encrypted", _encrypted(), "encrypted"),
        ("truncated", AFFIDAVIT[: len(AFFIDAVIT) // 3] + b"\n%%EOF", "corrupt"),
        ("junk", b"%PDF-1.7\n" + b"\x00\xff" * 300 + b"\n%%EOF", "corrupt"),
        ("zero pages", _zero_pages(), "no_pages"),
        ("blank", _blank(), "blank"),
        ("too many pages", _many_pages(), "too_large"),
    ],
)
def test_bad_inputs_never_500_and_land_on_manual_review(
    make_client: Factory, name: str, data: bytes, variant: str
) -> None:
    client = make_client(None)
    before = manual_tasks(client)
    r = client.post(URL, content=data, headers=HEADERS)
    assert r.status_code == 201, f"{name}: {r.text}"
    doc = affidavit_doc(r.json())
    assert doc["label"] == "manual_review_required", name
    assert doc["read"]["reason_code"] == "DOC_UNREADABLE" and doc["read"]["variant"] == variant
    assert doc["read"]["why"].endswith(".") and "{" not in doc["read"]["why"]
    types = [e["event_type"] for e in entries(client)]
    assert "document.read" in types and "manual_task.created" in types
    assert manual_tasks(client) == before + 1
    # every view of the case still answers
    for path in ("review", "affidavit-diff", "verification"):
        assert client.get(f"/v1/cases/{DCE05}/{path}", headers=auth(token())).status_code == 200
    assert client.get("/v1/alerts", headers=auth(token())).status_code == 200


def test_page_cap_is_recorded_as_skipped(make_client: Factory) -> None:
    client = make_client(None)
    r = client.post(URL, content=_many_pages(), headers=HEADERS)
    pages = affidavit_doc(r.json())["read"]["pages"]
    assert [p["kind"] for p in pages].count("skipped") == 10 and len(pages) == 60


def test_not_a_pdf_is_still_rejected_by_content_sniffing(make_client: Factory) -> None:
    client = make_client(None)
    r = client.post(URL, content=b"MZ\x90\x00 renamed executable", headers=HEADERS)
    assert r.status_code == 422 and r.json()["code"] == "UPLOAD_CONTENT_REJECTED"


@pytest.mark.parametrize("confidence", [1.0, 0.95, 0.5, 0.0])
def test_ocr_never_yields_verified(make_client: Factory, confidence: float) -> None:
    client = make_client(fake_from_source_pdf(AFFIDAVIT, confidence))
    r = client.post(URL, content=rasterise(AFFIDAVIT, dpi=150), headers=HEADERS)
    assert r.status_code == 201
    assert affidavit_doc(r.json())["label"] == "manual_review_required"
    assert r.json()["label_counts"]["verified"] <= 1  # the accounts statement may stay verified
    verification = client.get(f"/v1/cases/{DCE05}/verification", headers=auth(token())).json()
    scanned = next(d for d in verification["documents"] if d["slot"] == "annex2.1(i) affidavit")
    assert scanned["label"] == "manual_review_required"
    assert any(
        c["reason_code"] in ("SCAN_IMAGE_ONLY", "OCR_LOW_CONFIDENCE") for c in scanned["checks"]
    )


# ---- the three seeded scan cases (Demo Institute of Technology 13 and 17, College of Eng. 15) ----
DT13 = "cas_01JD3M5A00000000000000DT13"
DCE15 = "cas_01JD3M5A00000000000000CE15"
DT17 = "cas_01JD3M5A00000000000000DT17"


def _view(engine: FakeOcrEngine | None, case_id: str) -> dict:  # type: ignore[type-arg]
    import asyncio

    from satya_api.workflow import Workflow

    repo = FixtureCaseRepository(CASES, TOKEN_KEY, ocr_engine=engine)
    # One fake engine returns one document's text for every scan, so the register of current
    # filings is left out here (it would see that text three times); prior filings stay.
    repo._registry = Registry.from_file(repo.registry_file)
    return asyncio.run(Workflow(repo, MemoryStore(), None).view(case_id))


def _source(profile: int) -> bytes:
    from satya_forensics.synth.variants import AFFIDAVIT_FILE, build_case

    return build_case(profile, "clean").files[AFFIDAVIT_FILE]


def test_seeded_scans_without_an_engine_are_ocr_unavailable_and_low_band() -> None:
    for case_id in (DT13, DCE15, DT17):
        view = _view(None, case_id)
        doc = affidavit_doc(view)
        assert doc["label"] == "manual_review_required"
        assert doc["read"]["reason_code"] == "OCR_UNAVAILABLE"
        assert view["risk"]["band"] == "low" and len(view["tasks"]) == 1
    mixed = affidavit_doc(_view(None, DT17))["read"]["pages"]
    assert [p["kind"] for p in mixed] == ["text_layer", "image_only", "text_layer", "text_layer"]


def test_seeded_clean_and_mixed_scans_are_read_by_ocr() -> None:
    clean = _view(fake_from_source_pdf(_source(13), 0.93), DT13)
    assert affidavit_doc(clean)["read"]["status"] == "ocr_read"
    assert [f for f in clean["flags"] if f["rule_id"].startswith("AFF-")] == []
    assert clean["risk"]["band"] == "low"
    mixed = _view(fake_from_source_pdf(_source(17), 0.93), DT17)
    read = affidavit_doc(mixed)["read"]
    assert read["status"] == "ocr_read" and [
        p["page"] for p in read["pages"] if "ocr_confidence" in p
    ] == [2]
    assert affidavit_doc(mixed)["label"] == "manual_review_required"


def test_seeded_noisy_scan_falls_back_on_confidence() -> None:
    view = _view(fake_from_source_pdf(_source(15), 0.55), DCE15)
    doc = affidavit_doc(view)
    assert doc["read"]["reason_code"] == "OCR_LOW_CONFIDENCE" and doc["label"] != "verified"


# ---- O-23: a stamp number read by OCR is never a reuse finding ---------------------------------
DIT11 = "cas_01JD3M5A00000000000000DT11"
DIT11_PDF = (CASES / "dit11-2026-27" / "affidavit-sworn.pdf").read_bytes()


def test_ocr_stamp_number_never_enters_the_registry(make_client: Factory) -> None:
    import asyncio

    from satya_forensics.stamp import certificate_number
    from satya_forensics.textlayer import read_pages

    client = make_client(fake_from_source_pdf(AFFIDAVIT, 0.93))
    r = client.post(URL, content=rasterise(AFFIDAVIT, dpi=150, seed=3), headers=HEADERS)
    assert r.status_code == 201
    number = certificate_number(read_pages(AFFIDAVIT))
    assert number
    repo = client.app.state.cases  # type: ignore[attr-defined]
    registry = asyncio.run(repo.registry())
    assert registry.stamp_reused(number, "1-90000099999", "2026-27") == []


def test_ocr_number_matching_another_case_is_a_note_not_reuse(make_client: Factory) -> None:
    client = make_client(fake_from_source_pdf(DIT11_PDF, 0.9))
    r = client.post(URL, content=rasterise(DIT11_PDF, dpi=150, seed=4), headers=HEADERS)
    assert r.status_code == 201
    view = r.json()
    rules = {f["rule_id"]: f for f in view["flags"]}
    assert "STAMP-REUSE" not in rules
    note = rules["STAMP-OCR-MATCH"]
    assert note["label"] == "manual_review_required" and note["preliminary_indicator"] is True
    assert note["severity"] == "info"
    doc = affidavit_doc(view)
    assert doc["label"] == "manual_review_required"
    assert all(c["outcome"] != "mismatch_detected" for c in doc["checks"])
    assert all(c["reason_code"] != "SRC_BOUND_TO_OTHER_FILING" for c in doc["checks"])
    assert "STAMP-OCR-MATCH" not in {r["rule_id"] for r in view["risk"]["reasons"]}
    assert "document.note" in [e["event_type"] for e in entries(client)]


def test_native_stamp_reuse_still_raises_the_finding() -> None:
    view = _view(None, DIT11)
    rules = {f["rule_id"] for f in view["flags"]}
    assert "STAMP-REUSE" in rules and "STAMP-OCR-MATCH" not in rules
