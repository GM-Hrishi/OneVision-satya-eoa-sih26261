"""S2.4: issuer and uploader signature checks → VerificationResult.checks[] (Portal §2.7/§2.8)."""

from typing import Any

import pytest

from satya_forensics import pki
from satya_forensics.engine import AFFIDAVIT_SLOT
from satya_forensics.labels import document_label
from satya_forensics.registry import Registry
from satya_forensics.synth.variants import build_case
from satya_shared_types import validator

from .conftest import run_case


def _affidavit(result: Any) -> Any:
    return next(d for d in result.documents if d.slot == AFFIDAVIT_SLOT)


def _check(doc: Any, kind: str) -> dict[str, Any] | None:
    return next((c for c in doc.verification["checks"] if c["kind"] == kind), None)


@pytest.mark.parametrize(
    ("variant", "issuer_code", "issuer_outcome", "issuer_state"),
    [
        ("clean", "SIG_VALID", "verified", "verified"),
        ("sig_digest", "SIG_DIGEST_MISMATCH", "mismatch_detected", "chain_broken"),
        ("sig_modified", "SIG_MODIFIED_AFTER_SIGNING", "mismatch_detected", "edited_after_signing"),
        ("sig_revoked", "SIG_CERT_REVOKED", "mismatch_detected", "chain_broken"),
        ("sig_expired", "SIG_CERT_EXPIRED", "expired", "chain_broken"),
        ("sig_not_yet_valid", "SIG_CERT_EXPIRED", "expired", "chain_broken"),
        ("sig_untrusted", "SIG_UNTRUSTED_CHAIN", "manual_review_required", "chain_broken"),
        ("sig_image_only", "SIG_IMAGE_ONLY", "manual_review_required", "image_only"),
        ("sig_signer", "SIG_SIGNER_NOT_MATCHED", "manual_review_required", "chain_broken"),
        ("sig_revocation_down", "SIG_REVOCATION_UNREACHABLE", "source_unavailable", "chain_broken"),
    ],
)
def test_issuer_signature_outcomes(
    variant: str, issuer_code: str, issuer_outcome: str, issuer_state: str
) -> None:
    case = build_case(7, variant)
    doc = _affidavit(run_case(case))
    check = _check(doc, "issuer_signature")
    assert check is not None
    assert (check["reason_code"], check["outcome"]) == (issuer_code, issuer_outcome)
    assert doc.issuer_sig is not None and doc.issuer_sig["state"] == issuer_state
    assert doc.verification["label"] == case.truth["expected_document_labels"][doc.doc_id]
    assert list(validator("VerificationResult").iter_errors(doc.verification)) == []
    for sig in (doc.issuer_sig, doc.uploader_sig):
        assert list(validator("SignatureCheck").iter_errors(sig)) == []


def test_two_independent_checks_and_test_trust_anchor() -> None:
    doc = _affidavit(run_case(build_case(5, "clean")))
    issuer, uploader = _check(doc, "issuer_signature"), _check(doc, "uploader_signature")
    assert issuer and uploader
    assert issuer["trust_anchor_label"] == uploader["trust_anchor_label"] == "TEST TRUST ANCHOR"
    assert doc.uploader_sig == {
        "role": "uploader",
        "state": "present",
        "has_byte_range": True,
        "reason_code": "SIG_VALID",
        "signer_role": "chairman",
        "trust_anchor_label": "TEST TRUST ANCHOR",
    }
    assert doc.verification["label"] == "verified"
    assert issuer["signed_at"] < uploader["signed_at"]


def test_valid_uploader_never_makes_a_document_verified() -> None:
    doc = _affidavit(run_case(build_case(9, "sig_image_only")))
    assert _check(doc, "uploader_signature") == {
        "kind": "uploader_signature",
        "outcome": "verified",
        "reason_code": "SIG_VALID",
        "signed_at": _check(doc, "uploader_signature")["signed_at"],  # type: ignore[index]
        "trust_anchor_label": "TEST TRUST ANCHOR",
        "attempts": 1,  # one CRL fetch from the mock endpoint
    }
    assert doc.verification["label"] == "manual_review_required"
    assert doc.issuer_sig is not None and doc.issuer_sig["has_byte_range"] is False
    # Only an uploader check and passing format checks: still not verified.
    checks = [
        {"kind": "uploader_signature", "outcome": "verified"},
        {"kind": "format", "outcome": "verified"},
    ]
    assert document_label(checks) == "manual_review_required"
    assert (
        document_label([*checks, {"kind": "issuer_signature", "outcome": "verified"}]) == "verified"
    )


def test_label_precedence() -> None:
    def label(*outcomes: str) -> str:
        return document_label({"kind": "issuer_signature", "outcome": o} for o in outcomes)

    assert (
        label("verified", "source_unavailable", "manual_review_required")
        == "manual_review_required"
    )
    assert label("expired", "mismatch_detected") == "mismatch_detected"
    assert label("verification_pending", "verified") == "verification_pending"
    assert label("source_unavailable", "expired") == "expired"
    assert document_label([]) == "verification_pending"


def test_uploader_missing_is_a_flag_not_a_label() -> None:
    result = run_case(build_case(11, "uploader_missing"))
    doc = _affidavit(result)
    assert _check(doc, "uploader_signature") is None
    assert doc.uploader_sig is not None and doc.uploader_sig["state"] == "absent_required"
    assert (
        doc.verification["label"] == "verified"
    )  # issuer signature verified; no label from the gap
    flag = next(f for f in doc.flags if f["rule_id"] == "SIG-UPLOADER-MISSING")
    assert flag["check_ref"] == "m6:SIG-UPLOADER-MISSING:uploader"
    assert list(validator("Flag").iter_errors(flag)) == []


def test_benign_updates_and_noisy_controls_raise_nothing() -> None:
    for variant in (
        "clean_benign_dss",
        "clean_benign_info",
        "clean_odd_metadata",
        "clean_revoked_late",
        "clean_cert_edge",
        "clean_visible_sig",
    ):
        doc = _affidavit(run_case(build_case(13, variant)))
        assert doc.flags == [], (variant, [f["check_ref"] for f in doc.flags])
        assert doc.verification["label"] == "verified", variant


def test_revocation_retries_then_source_unavailable() -> None:
    case = build_case(15, "sig_revocation_down")
    endpoints = pki.standard_crl_endpoints(list(case.crl_specs))
    from satya_forensics.engine import M6Input, run
    from satya_forensics.signatures import TrustStore
    from satya_forensics.synth.variants import prior_filings

    from .conftest import CHECKED_AT, KEY

    files = {d["doc_id"]: case.files[d["file"]] for d in case.case["documents"]}
    result = run(
        M6Input(
            case.case,
            case.snapshot,
            files,
            KEY,
            TrustStore.test_anchor(),
            endpoints,
            Registry.from_json(prior_filings()),
            CHECKED_AT,
        )
    )
    check = _check(_affidavit(result), "issuer_signature")
    assert check is not None and check["attempts"] == 3
    assert endpoints.calls[pki.CRL_DOWN_URL] == 3


def test_flags_cite_rules_and_are_deterministic() -> None:
    case = build_case(3, "sig_modified")
    a, b = run_case(case), run_case(case)
    assert a.flags == b.flags
    for flag in a.flags:
        assert flag["aph_clause"] == "2.3.4a"
        assert flag["provenance"] == "satya" and flag["disposition"] is None
        assert flag["preliminary_indicator"] is True
        assert list(validator("Flag").iter_errors(flag)) == []
