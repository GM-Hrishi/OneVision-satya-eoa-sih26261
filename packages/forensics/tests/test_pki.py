"""S2.1: the synthetic test PKI (TEST TRUST ANCHOR) is reproducible, well-formed and test-only."""

from datetime import UTC, datetime, timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.x509.oid import NameOID

from satya_forensics import pki

T = datetime(2026, 11, 23, 4, 45, tzinfo=UTC)


def _spec(kind: str, profile: int = 3) -> pki.SignerSpec:
    return pki.signer_spec(kind, profile, "Demo Trustee 03", T)


def _verify(child: x509.Certificate, parent: x509.Certificate) -> None:
    key = parent.public_key()
    assert isinstance(key, Ed25519PublicKey)
    key.verify(child.signature, child.tbs_certificate_bytes)


def test_hierarchy_names_and_chain() -> None:
    root, sub = pki.trust_anchor(), pki.intermediate()
    assert root.common_name == pki.TRUST_ANCHOR_CN == "SATYA TEST TRUST ANCHOR"
    assert root.cert.subject == root.cert.issuer
    _verify(root.cert, root.cert)
    _verify(sub.cert, root.cert)
    signer = pki.signer(_spec("chairman"))
    _verify(signer.cert, sub.cert)
    assert signer.common_name == "Demo Trustee 03"
    for cert in (root.cert, sub.cert, signer.cert):
        org = cert.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value
        assert "synthetic test PKI (not a real CA)" in str(org)


def test_reproducible_without_stored_keys() -> None:
    first = pki.signer(_spec("revoked")).cert_pem()
    pki._signer.cache_clear()
    assert pki.signer(_spec("revoked")).cert_pem() == first
    assert pki.build_crl({5: T}) == pki.build_crl({5: T})


@pytest.mark.parametrize(
    ("kind", "valid_at_signing"),
    [
        ("chairman", True),
        ("edge", True),
        ("revoked-late", True),
        ("expired", False),
        ("not-yet-valid", False),
    ],
)
def test_validity_windows(kind: str, valid_at_signing: bool) -> None:
    cert = pki.signer(_spec(kind)).cert
    inside = cert.not_valid_before_utc <= T <= cert.not_valid_after_utc
    assert inside is valid_at_signing
    if kind == "edge":
        assert cert.not_valid_after_utc - T == timedelta(days=1)


def test_wrong_signer_and_untrusted() -> None:
    wrong = pki.signer(_spec("wrong-signer"))
    assert wrong.common_name != "Demo Trustee 03"
    _verify(wrong.cert, pki.intermediate().cert)
    untrusted = pki.signer(_spec("untrusted"))
    assert untrusted.cert.issuer == untrusted.cert.subject
    assert "UNTRUSTED" in untrusted.common_name


def test_crl_lists_revoked_serials_and_down_endpoint_is_absent() -> None:
    specs = [_spec(k) for k in ("chairman", "revoked", "revoked-late", "crl-down")]
    endpoints = pki.standard_crl_endpoints(specs)
    raw = endpoints.fetch(pki.CRL_URL)
    assert raw is not None
    crl = x509.load_der_x509_crl(raw)
    serials = {r.serial_number: r.revocation_date_utc for r in crl}
    revoked = pki.signer(_spec("revoked")).cert
    late = pki.signer(_spec("revoked-late")).cert
    assert serials[revoked.serial_number] < T < serials[late.serial_number]
    assert pki.signer(_spec("chairman")).cert.serial_number not in serials
    assert crl.is_signature_valid(pki.intermediate().cert.public_key())  # type: ignore[arg-type]
    down = pki.signer(_spec("crl-down")).cert
    dp = down.extensions.get_extension_for_class(x509.CRLDistributionPoints).value
    assert dp[0].full_name[0].value == pki.CRL_DOWN_URL  # type: ignore[index, union-attr]
    assert endpoints.fetch(pki.CRL_DOWN_URL) is None
    assert endpoints.calls[pki.CRL_DOWN_URL] == 1


def test_cli_writes_only_public_material(tmp_path: object) -> None:
    from pathlib import Path

    out = Path(str(tmp_path))
    assert pki.main(["--out", str(out)]) == 0
    names = sorted(p.name for p in out.iterdir())
    assert names == ["satya-test-root.pem", "satya-test-sub-ca-1.crl", "satya-test-sub-ca-1.pem"]
    for path in out.iterdir():
        assert b"PRIVATE KEY" not in path.read_bytes()
