"""Synthetic test PKI for M6 (tests and demo only; never real CA material).

Hierarchy (every name says TEST and SATYA, nothing imitates a real CA or a licensed CA's DSC):

    SATYA TEST TRUST ANCHOR (root, self-signed)
    └── SATYA TEST SUB-CA 1 (intermediate; issues the signer certs and the CRL)
        ├── chairman-<nn> / secretary-<nn>   valid, the authorised signatory of profile nn
        ├── wrong-signer-<nn>                valid chain, not the authorised signatory
        ├── expired-<nn>                     validity ended before the signing time
        ├── edge-<nn>                        valid; expires one day after the signing time (control)
        ├── not-yet-valid-<nn>               validity starts after the signing time
        ├── revoked-<nn>                     on the CRL, revoked before the signing time
        ├── revoked-late-<nn>                on the CRL, revoked after the signing time (control)
        └── crl-down-<nn>                    CRL distribution point that never answers
    SATYA TEST UNTRUSTED SELF-SIGNED <nn>    self-signed, outside the trust store

Keys are Ed25519 derived from public seeds (`SATYA TEST PKI | <name>`), so certificates, the CRL
and every signature are byte-for-byte reproducible and no private key is ever stored in the repo:
a key is regenerated from its seed when a test or the generator needs it. Anyone can derive these
keys, which is the point: they prove nothing outside this test suite.

The CRL lives behind a mock endpoint registry (`MockCrlEndpoints`) so revocation can be "up",
"revoked" or "unreachable" without any network access.
"""

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from functools import cache

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

TRUST_ANCHOR_CN = "SATYA TEST TRUST ANCHOR"
TRUST_ANCHOR_LABEL = "TEST TRUST ANCHOR"  # shown in the UI for every demo chain (guard rail 10)
INTERMEDIATE_CN = "SATYA TEST SUB-CA 1"
ORG = "SATYA-EoA synthetic test PKI (not a real CA)"
CRL_URL = "http://crl.satya-test.invalid/sub-ca-1.crl"
CRL_DOWN_URL = "http://crl-down.satya-test.invalid/sub-ca-1.crl"
# The whole test PKI is anchored in fixed dates so every fixture is reproducible.
EPOCH = datetime(2024, 1, 1, tzinfo=UTC)
CRL_THIS_UPDATE = datetime(2026, 11, 1, tzinfo=UTC)
CRL_NEXT_UPDATE = datetime(2027, 11, 1, tzinfo=UTC)

KINDS = (
    "chairman",
    "secretary",
    "wrong-signer",
    "expired",
    "edge",
    "not-yet-valid",
    "revoked",
    "revoked-late",
    "crl-down",
    "untrusted",
)


def _key(name: str) -> Ed25519PrivateKey:
    seed = hashlib.sha256(f"SATYA TEST PKI | {name}".encode()).digest()
    return Ed25519PrivateKey.from_private_bytes(seed)


def _serial(name: str) -> int:
    return int.from_bytes(hashlib.sha256(f"serial | {name}".encode()).digest()[:15], "big") | 1


def _name(cn: str, role: str | None = None) -> x509.Name:
    attrs = [
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, ORG),
        x509.NameAttribute(NameOID.COMMON_NAME, cn),
    ]
    if role:
        attrs.insert(2, x509.NameAttribute(NameOID.TITLE, role))
    return x509.Name(attrs)


@dataclass(frozen=True)
class Identity:
    """A certificate plus the means to regenerate its key."""

    name: str
    cert: x509.Certificate
    key_name: str

    @property
    def key(self) -> Ed25519PrivateKey:
        return _key(self.key_name)

    @property
    def common_name(self) -> str:
        value = self.cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        return value if isinstance(value, str) else value.decode()

    def cert_pem(self) -> bytes:
        return self.cert.public_bytes(serialization.Encoding.PEM)

    def key_pem(self) -> bytes:
        return self.key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )


@dataclass(frozen=True)
class SignerSpec:
    """Why a signer cert exists, and the person it names (always a synthetic name)."""

    kind: str
    profile: int
    common_name: str
    role: str
    not_before: datetime
    not_after: datetime
    crl_url: str = CRL_URL
    revoked_at: datetime | None = None


def signer_spec(kind: str, profile: int, signatory_name: str, signing_time: datetime) -> SignerSpec:
    """The signer cert of `kind` for synthetic profile `profile`, relative to the signing time."""
    if kind not in KINDS:
        raise KeyError(f"unknown test signer kind {kind}")
    nb, na = signing_time - timedelta(days=365), signing_time + timedelta(days=365)
    cn, role = signatory_name, "Chairman"
    revoked_at = None
    crl = CRL_URL
    match kind:
        case "secretary":
            role = "Secretary"
        case "wrong-signer":
            cn, role = f"Demo Office Assistant {profile:02d}", "Office Assistant"
        case "expired":
            nb, na = signing_time - timedelta(days=730), signing_time - timedelta(days=3)
        case "edge":
            nb, na = signing_time - timedelta(days=729), signing_time + timedelta(days=1)
        case "not-yet-valid":
            nb, na = signing_time + timedelta(days=3), signing_time + timedelta(days=730)
        case "revoked":
            revoked_at = signing_time - timedelta(days=10)
        case "revoked-late":
            revoked_at = signing_time + timedelta(days=10)
        case "crl-down":
            crl = CRL_DOWN_URL
    return SignerSpec(kind, profile, cn, role, nb, na, crl, revoked_at)


def _builder(
    subject: x509.Name, issuer: x509.Name, name: str, nb: datetime, na: datetime
) -> x509.CertificateBuilder:
    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .serial_number(_serial(name))
        .not_valid_before(nb)
        .not_valid_after(na)
    )


@cache
def trust_anchor() -> Identity:
    key = _key("root")
    name = _name(TRUST_ANCHOR_CN)
    cert = (
        _builder(name, name, "root", EPOCH, EPOCH + timedelta(days=365 * 20))
        .public_key(key.public_key())
        .add_extension(x509.BasicConstraints(ca=True, path_length=1), critical=True)
        .add_extension(
            x509.KeyUsage(False, False, False, False, False, True, True, False, False),
            critical=True,
        )
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
        .sign(key, None)
    )
    return Identity("root", cert, "root")


@cache
def intermediate() -> Identity:
    root = trust_anchor()
    key = _key("sub-ca-1")
    cert = (
        _builder(
            _name(INTERMEDIATE_CN),
            root.cert.subject,
            "sub-ca-1",
            EPOCH,
            EPOCH + timedelta(days=365 * 10),
        )
        .public_key(key.public_key())
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(False, False, False, False, False, True, True, False, False),
            critical=True,
        )
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(root.key.public_key()), False
        )
        .sign(root.key, None)
    )
    return Identity("sub-ca-1", cert, "sub-ca-1")


def _signer_extensions(builder: x509.CertificateBuilder, crl_url: str) -> x509.CertificateBuilder:
    return (
        builder.add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(True, True, False, False, False, False, False, False, False),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.EMAIL_PROTECTION]), critical=False
        )
        .add_extension(
            x509.CRLDistributionPoints(
                [
                    x509.DistributionPoint(
                        [x509.UniformResourceIdentifier(crl_url)], None, None, None
                    )
                ]
            ),
            critical=False,
        )
    )


@cache
def _signer(spec: SignerSpec) -> Identity:
    name = f"{spec.kind}-{spec.profile:02d}"
    key = _key(name)
    if spec.kind == "untrusted":
        subject = _name(f"SATYA TEST UNTRUSTED SELF-SIGNED {spec.profile:02d}", spec.role)
        builder = _builder(subject, subject, name, spec.not_before, spec.not_after)
        cert = _signer_extensions(builder.public_key(key.public_key()), spec.crl_url).sign(
            key, None
        )
        return Identity(name, cert, name)
    ca = intermediate()
    builder = _builder(
        _name(spec.common_name, spec.role), ca.cert.subject, name, spec.not_before, spec.not_after
    ).public_key(key.public_key())
    builder = _signer_extensions(builder, spec.crl_url).add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_public_key(ca.key.public_key()), False
    )
    return Identity(name, builder.sign(ca.key, None), name)


def signer(spec: SignerSpec) -> Identity:
    return _signer(spec)


def build_crl(revoked: Mapping[int, datetime]) -> bytes:
    """DER CRL from the intermediate, listing `serial -> revocation time`."""
    ca = intermediate()
    builder = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(ca.cert.subject)
        .last_update(CRL_THIS_UPDATE)
        .next_update(CRL_NEXT_UPDATE)
        .add_extension(x509.CRLNumber(1), critical=False)
    )
    for serial, when in sorted(revoked.items()):
        builder = builder.add_revoked_certificate(
            x509.RevokedCertificateBuilder()
            .serial_number(serial)
            .revocation_date(when)
            .add_extension(x509.CRLReason(x509.ReasonFlags.key_compromise), critical=False)
            .build()
        )
    return builder.sign(ca.key, None).public_bytes(serialization.Encoding.DER)


@dataclass
class MockCrlEndpoints:
    """Stand-in for CRL distribution points: URL -> DER CRL. A URL that is not here never answers.

    `calls` counts fetch attempts so tests can see the retries (Portal §2.11).
    """

    crls: dict[str, bytes] = field(default_factory=dict)
    calls: dict[str, int] = field(default_factory=dict)

    def fetch(self, url: str) -> bytes | None:
        self.calls[url] = self.calls.get(url, 0) + 1
        return self.crls.get(url)


def standard_crl_endpoints(specs: list[SignerSpec]) -> MockCrlEndpoints:
    """The test CRL endpoint with every revoked test cert among `specs` (the down URL is absent)."""
    revoked = {}
    for spec in specs:
        if spec.revoked_at is not None:
            revoked[signer(spec).cert.serial_number] = spec.revoked_at
    return MockCrlEndpoints({CRL_URL: build_crl(revoked)})


def certificate_pems() -> dict[str, bytes]:
    """Root and intermediate certificates (public material) for docs and the trust store."""
    return {"root": trust_anchor().cert_pem(), "sub-ca-1": intermediate().cert_pem()}


def main(argv: list[str] | None = None) -> int:
    """Write the public half of the test PKI (root, intermediate, empty CRL) to a directory.

    Private keys are never written: they are derived from public seeds whenever needed.
    """
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, pem in certificate_pems().items():
        (args.out / f"satya-test-{name}.pem").write_bytes(pem)
    (args.out / "satya-test-sub-ca-1.crl").write_bytes(build_crl({}))
    print(f"wrote the public SATYA test PKI to {args.out} (TEST TRUST ANCHOR; synthetic only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
