"""Issuer and uploader signature checks (Portal spec §2.8, design C3, decisions #16, #28, #31).

For every real CMS signature (/ByteRange) in a PDF, in this order (most severe first):

1. digest: the signed byte range still hashes to the signed digest (pyHanko `intact`/`valid`);
2. modified after signing: a later revision changes more than a signature permits. pyHanko's
   modification analysis (`PdfSignatureStatus.coverage`, `.modification_level`, `.docmdp_ok`;
   confirmed for pyHanko 0.38 [V-8]) calls DSS/Info updates `LTA_UPDATES` and later signatures
   `FORM_FILLING`; only `OTHER` (e.g. new page content) or a DocMDP violation is flagged;
3. revoked before the signing time (CRL of the issuing CA, fetched with retries);
4. certificate expired or not yet valid at the signing time;
5. chain does not build to a configured trust anchor;
6. signer is not the authorised Chairman/Secretary (keyed token of the certificate's name);
7. CRL unreachable after retries;
otherwise SIG_VALID.

The validation moment is the signing time the signer claims (CMS signingTime); there is no
timestamp authority in the demo PKI [VERIFY: production should require a TSA token or LTV data].

Which signature is whose (decision recorded in progress/DECISIONS-SLICE-2):
- Affidavit (the deponent and the uploader are both the authorised signatory): real signatures are
  taken in revision order. With two or more, the first is the issuer's (the deponent signs the
  affidavit) and the last is the uploader's (the institution's DSC on the compiled file). With
  one, it is the uploader's when a separate printed mark claims to be the issuer's signature,
  otherwise the issuer's (and the uploader DSC is missing).
- External documents (issued by an authority, e.g. audited accounts, licences): the last signature
  by the authorised signatory (token match) is the uploader's; the first other signature is the
  issuing authority's. The signer check applies to the uploader only.
A printed "Digitally signed by" mark that is not the appearance of a real signature is always
IMAGE ONLY and never verified.
"""

import io
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from asn1crypto import x509 as asn1_x509
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.diff_analysis import ModificationLevel
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko.sign.validation.pdf_embedded import EmbeddedPdfSignature
from pyhanko.sign.validation.status import SignatureCoverageLevel
from pyhanko_certvalidator import ValidationContext

from satya_affidavit.ids import token
from satya_forensics import pki
from satya_forensics.textlayer import Box, Mark, Page

# Expected failures (expired, untrusted, …) are reported as reason codes, not as log tracebacks.
for _name in ("pyhanko", "pyhanko_certvalidator"):
    logging.getLogger(_name).setLevel(logging.CRITICAL)

OUTCOME = {
    "SIG_VALID": "verified",
    "SIG_DIGEST_MISMATCH": "mismatch_detected",
    "SIG_MODIFIED_AFTER_SIGNING": "mismatch_detected",
    "SIG_CERT_REVOKED": "mismatch_detected",
    "SIG_CERT_EXPIRED": "expired",
    "SIG_UNTRUSTED_CHAIN": "manual_review_required",
    "SIG_IMAGE_ONLY": "manual_review_required",
    "SIG_SIGNER_NOT_MATCHED": "manual_review_required",
    "SIG_REVOCATION_UNREACHABLE": "source_unavailable",
    "SIG_NOT_DIGITAL": "manual_review_required",
}
ISSUER_STATE = {
    "SIG_VALID": "verified",
    "SIG_IMAGE_ONLY": "image_only",
    "SIG_MODIFIED_AFTER_SIGNING": "edited_after_signing",
    "SIG_NOT_DIGITAL": "not_digital",
}


class RevocationSource(Protocol):
    def fetch(self, url: str) -> bytes | None: ...


@dataclass(frozen=True)
class TrustStore:
    roots: tuple[x509.Certificate, ...]
    intermediates: tuple[x509.Certificate, ...]
    label: str

    @classmethod
    def test_anchor(cls) -> "TrustStore":
        return cls((pki.trust_anchor().cert,), (pki.intermediate().cert,), pki.TRUST_ANCHOR_LABEL)

    @classmethod
    def from_pem_dir(cls, directory: Path, label: str = pki.TRUST_ANCHOR_LABEL) -> "TrustStore":
        roots: list[x509.Certificate] = []
        others: list[x509.Certificate] = []
        for path in sorted(directory.glob("*.pem")):
            cert = x509.load_pem_x509_certificate(path.read_bytes())
            (roots if cert.subject == cert.issuer else others).append(cert)
        return cls(tuple(roots), tuple(others), label)


@dataclass(frozen=True)
class SigResult:
    """One signature check (issuer or uploader) before it becomes a Check / SignatureCheck."""

    role: str  # issuer | uploader
    reason_code: str  # SIG_* or UPLOADER_DSC_MISSING
    has_byte_range: bool
    field_name: str | None = None
    page: int | None = None
    regions: list[dict[str, float]] = field(default_factory=list)
    signed_at: datetime | None = None
    signer_role: str | None = None
    trust_anchor_label: str | None = None
    revocation_attempts: int = 0
    revision: int | None = None
    signer_matches: bool | None = None
    extracted: Any = None  # what the finding shows as "extracted" (signer, time, …)
    expected: Any = None

    @property
    def outcome(self) -> str | None:
        return OUTCOME.get(self.reason_code)

    @property
    def present(self) -> bool:
        return self.reason_code != "UPLOADER_DSC_MISSING"


@dataclass(frozen=True)
class SignatureContext:
    trust: TrustStore
    revocation: RevocationSource
    token_key: bytes
    signatory_token: str | None
    retries: int = 3


def _der(cert: x509.Certificate) -> asn1_x509.Certificate:
    return asn1_x509.Certificate.load(cert.public_bytes(serialization.Encoding.DER))


def _crypto(cert: asn1_x509.Certificate) -> x509.Certificate:
    return x509.load_der_x509_certificate(cert.dump())


def _issued_by(child: x509.Certificate, parent: x509.Certificate) -> bool:
    try:
        child.verify_directly_issued_by(parent)
    except (ValueError, TypeError, Exception):
        return False
    return True


def _chain(
    cert: x509.Certificate, trust: TrustStore, extra: Sequence[x509.Certificate]
) -> tuple[bool, x509.Certificate | None]:
    """(builds to a trust root, direct issuer if found). Path length is capped at five."""
    pool = [*trust.intermediates, *extra]
    current, issuer = cert, None
    for _ in range(5):
        for root in trust.roots:
            if current.issuer == root.subject and _issued_by(current, root):
                return True, issuer or root
        parent = next(
            (
                c
                for c in pool
                if c.subject == current.issuer and c != current and _issued_by(current, c)
            ),
            None,
        )
        if parent is None:
            return False, issuer
        issuer = issuer or parent
        current = parent
    return False, issuer


def _crl_urls(cert: x509.Certificate) -> list[str]:
    try:
        ext = cert.extensions.get_extension_for_class(x509.CRLDistributionPoints).value
    except x509.ExtensionNotFound:
        return []
    return [
        name.value
        for dp in ext
        for name in (dp.full_name or [])
        if isinstance(name, x509.UniformResourceIdentifier)
    ]


def _revocation(
    cert: x509.Certificate, issuer: x509.Certificate, ctx: SignatureContext, at: datetime
) -> tuple[str, int]:
    """("ok" | "revoked" | "unreachable", attempts)."""
    urls = _crl_urls(cert)
    if not urls:
        return "unreachable", 0
    attempts = 0
    for url in urls:
        for _ in range(max(ctx.retries, 1)):
            attempts += 1
            raw = ctx.revocation.fetch(url)
            if raw is None:
                continue
            try:
                crl = x509.load_der_x509_crl(raw)
            except ValueError:
                continue
            if crl.issuer != issuer.subject or not crl.is_signature_valid(
                issuer.public_key()  # type: ignore[arg-type]
            ):
                continue
            entry = crl.get_revoked_certificate_by_serial_number(cert.serial_number)
            if entry is not None and entry.revocation_date_utc <= at:
                return "revoked", attempts
            return "ok", attempts
    return "unreachable", attempts


def _subject(cert: x509.Certificate, oid: x509.ObjectIdentifier) -> str | None:
    attrs = cert.subject.get_attributes_for_oid(oid)
    if not attrs:
        return None
    value = attrs[0].value
    return value if isinstance(value, str) else value.decode()


def _signer_role(cert: x509.Certificate) -> str:
    title = (_subject(cert, NameOID.TITLE) or "").casefold()
    if "chairman" in title:
        return "chairman"
    if "secretary" in title:
        return "secretary"
    return "unknown"


def _ref_key(obj: Any) -> tuple[int, int] | None:
    ref = getattr(obj, "reference", obj)
    idnum, generation = getattr(ref, "idnum", None), getattr(ref, "generation", 0)
    return None if idnum is None else (int(idnum), int(generation))


def _widget(
    sig: EmbeddedPdfSignature, pages: list[Page], refs: list[Any]
) -> tuple[int | None, Box | None]:
    """Page (1-based) and box (top-left origin) of a visible signature widget."""
    widget = sig.sig_field
    rect = widget.get("/Rect")
    page_ref = widget.raw_get("/P") if "/P" in widget else None
    if rect is None or page_ref is None:
        return None, None
    x0, y0, x1, y1 = (float(v) for v in rect)
    if x1 - x0 <= 0 or y1 - y0 <= 0:
        return None, None
    try:
        index = refs.index(_ref_key(page_ref))
    except ValueError:
        return None, None
    page = pages[index] if index < len(pages) else None
    if page is None:
        return index + 1, None
    return index + 1, Box(
        min(x0, x1), page.height - max(y0, y1), max(x0, x1), page.height - min(y0, y1)
    )


def validate_one(
    sig: EmbeddedPdfSignature, ctx: SignatureContext, check_signer: bool = True
) -> SigResult:
    """The reason code of one real signature, most severe finding first (module docstring)."""
    signed_at = sig.self_reported_timestamp
    base = SigResult(
        role="unknown",
        reason_code="SIG_VALID",
        has_byte_range=True,
        field_name=sig.field_name,
        signed_at=signed_at,
        revision=sig.signed_revision,
    )
    vc = ValidationContext(
        trust_roots=[_der(c) for c in ctx.trust.roots],
        other_certs=[_der(c) for c in ctx.trust.intermediates],
        moment=signed_at,
        allow_fetching=False,
        revocation_mode="soft-fail",
    )
    try:
        status = validate_pdf_signature(sig, vc)
    except Exception:
        return replace(base, reason_code="SIG_DIGEST_MISMATCH")
    if not status.intact or not status.valid:
        return replace(base, reason_code="SIG_DIGEST_MISMATCH")
    if status.coverage != SignatureCoverageLevel.ENTIRE_FILE and (
        status.modification_level is None
        or status.modification_level >= ModificationLevel.OTHER
        or not status.docmdp_ok
    ):
        level = status.modification_level.name if status.modification_level else "UNKNOWN"
        return replace(base, reason_code="SIG_MODIFIED_AFTER_SIGNING", extracted=level)
    cert = _crypto(status.signing_cert)
    embedded = [_crypto(c) for c in sig.other_embedded_certs]
    trusted, issuer = _chain(cert, ctx.trust, embedded)
    name = (_subject(cert, NameOID.COMMON_NAME) or "").strip()
    matches = None
    if ctx.signatory_token is not None:
        matches = token(ctx.token_key, name) == ctx.signatory_token
    base = replace(
        base,
        signer_role=_signer_role(cert),
        trust_anchor_label=ctx.trust.label if trusted else None,
        signer_matches=matches,
    )
    at = signed_at or datetime.now().astimezone()
    revocation, attempts = ("unreachable", 0)
    if trusted and issuer is not None:
        revocation, attempts = _revocation(cert, issuer, ctx, at)
    base = replace(base, revocation_attempts=attempts)
    if revocation == "revoked":
        return replace(base, reason_code="SIG_CERT_REVOKED")
    if not (cert.not_valid_before_utc <= at <= cert.not_valid_after_utc):
        window = f"{cert.not_valid_before_utc.date()}..{cert.not_valid_after_utc.date()}"
        return replace(base, reason_code="SIG_CERT_EXPIRED", extracted=window)
    if not trusted or (status.trust_problem_indic is not None and not status.bottom_line):
        return replace(base, reason_code="SIG_UNTRUSTED_CHAIN", trust_anchor_label=None)
    if check_signer and matches is False:
        return replace(
            base, reason_code="SIG_SIGNER_NOT_MATCHED", extracted="not the authorised signatory"
        )
    if revocation == "unreachable":
        return replace(base, reason_code="SIG_REVOCATION_UNREACHABLE")
    return base


@dataclass(frozen=True)
class SignatureReport:
    issuer: SigResult
    uploader: SigResult
    marks: list[Mark]  # printed marks that are not the appearance of a real signature
    real_count: int


def inspect(
    pdf: bytes,
    pages: list[Page],
    marks: list[Mark],
    ctx: SignatureContext,
    external: bool = False,
) -> SignatureReport:
    """Both signature checks of one document (issuer, uploader); see the module docstring."""
    reader = PdfFileReader(io.BytesIO(pdf), strict=False)
    refs = [_ref_key(reader.find_page_for_modification(i)[0]) for i in range(len(pages))]
    found: list[SigResult] = []
    widgets: list[tuple[int | None, Box | None]] = []
    for sig in sorted(reader.embedded_regular_signatures, key=lambda s: s.signed_revision):
        result = validate_one(sig, ctx, check_signer=not external)
        page, box = _widget(sig, pages, refs)
        if page is not None and box is not None:
            result = replace(result, page=page, regions=[pages[page - 1].region(box)])
        found.append(result)
        widgets.append((page, box))
    # A mark under a real signature's widget is that signature's appearance, not an image.
    printed = [
        m
        for m in marks
        if not any(
            page == m.page and box is not None and box.intersects(m.box) for page, box in widgets
        )
    ]
    image = None
    if printed:
        m = printed[-1]
        image = SigResult(
            role="issuer",
            reason_code="SIG_IMAGE_ONLY",
            has_byte_range=False,
            page=m.page,
            regions=[pages[m.page - 1].region(m.box)],
            signed_at=m.signed_at,
            extracted="printed mark without /ByteRange",  # the name on the mark is not copied
        )
    missing = SigResult(role="uploader", reason_code="UPLOADER_DSC_MISSING", has_byte_range=False)
    if external:
        mine = [r for r in found if r.signer_matches is not False]
        up = mine[-1] if mine else None
        others = [r for r in found if r is not up]
        issuer = (
            replace(others[0], role="issuer")
            if others
            else image
            or SigResult(role="issuer", reason_code="SIG_NOT_DIGITAL", has_byte_range=False)
        )
        uploader = replace(up, role="uploader") if up else missing
        return SignatureReport(issuer, uploader, printed, len(found))
    if len(found) >= 2:
        issuer, uploader = replace(found[0], role="issuer"), replace(found[-1], role="uploader")
    elif len(found) == 1 and image is not None:
        issuer, uploader = image, replace(found[0], role="uploader")
    elif len(found) == 1:
        issuer, uploader = replace(found[0], role="issuer"), missing
    else:
        issuer = image or SigResult(
            role="issuer", reason_code="SIG_NOT_DIGITAL", has_byte_range=False
        )
        uploader = missing
    return SignatureReport(issuer=issuer, uploader=uploader, marks=printed, real_count=len(found))


def signature_check(result: SigResult) -> dict[str, Any]:
    """The `SignatureCheck` badge object (document.schema.json, UI §4.3)."""
    if result.role == "issuer":
        state = ISSUER_STATE.get(result.reason_code, "chain_broken")
    elif not result.present:
        state = "absent_required"
    elif not result.has_byte_range:
        state = "image_only"
    else:
        state = "present"
    out: dict[str, Any] = {
        "role": result.role,
        "state": state,
        "has_byte_range": result.has_byte_range,
        "reason_code": result.reason_code,
    }
    if result.page is not None:
        out["page"] = result.page
    if result.signer_role is not None:
        out["signer_role"] = result.signer_role
    if result.trust_anchor_label is not None:
        out["trust_anchor_label"] = result.trust_anchor_label
    return out


def issuer_not_digital(page: int | None = None) -> SigResult:
    """Issuer of a document whose own signature is a wet seal (e.g. the CA on audited accounts)."""
    return SigResult(role="issuer", reason_code="SIG_NOT_DIGITAL", has_byte_range=False, page=page)
