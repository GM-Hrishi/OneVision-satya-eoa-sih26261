"""Sign and edit synthetic PDFs with pyHanko, reproducibly (tests and demo fixtures only).

Three things make pyHanko output vary between runs: the signing time and the /ModDate it writes
into the Info dictionary and XMP metadata (both taken from the clock), and the second half of the
trailer /ID (random). All are pinned here so a generated fixture is identical byte for byte on
every run, which `make synth-check` relies on.
"""

import dataclasses
import hashlib
import io
from datetime import datetime, timedelta, timezone
from typing import Any

from asn1crypto import crl as asn1_crl
from asn1crypto import keys as asn1_keys
from asn1crypto import x509 as asn1_x509
from cryptography.hazmat.primitives import serialization
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.metadata.model import DocumentMetadata
from pyhanko.sign import fields, signers
from pyhanko.sign.signers.pdf_signer import PdfSigner
from pyhanko.sign.validation.dss import DocumentSecurityStore
from pyhanko_certvalidator.registry import SimpleCertificateStore

from satya_forensics import pki

# Edits after signing are stamped at a fixed synthetic time (IST) so fixtures stay reproducible.
PINNED_EDIT_TIME = datetime(2026, 11, 26, 12, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))


class _PinnedMeta(DocumentMetadata):
    """Document metadata whose 'now' is a fixed time (pyHanko sets last_modified = 'now')."""

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "last_modified" and value == "now":
            value = self.__dict__.get("_pinned", value)
        super().__setattr__(name, value)


class _Writer(IncrementalPdfFileWriter):
    def __init__(self, stream: io.BytesIO, modified: datetime) -> None:
        super().__init__(stream)
        meta = _PinnedMeta(
            **{f.name: getattr(self._meta, f.name) for f in dataclasses.fields(self._meta)}
        )
        meta.__dict__["_pinned"] = modified
        self._meta = meta

    @classmethod
    def _handle_id(cls, prev: Any) -> generic.ArrayObject:
        first = super()._handle_id(prev)[0]
        digest = hashlib.sha256(b"satya-synthetic-revision" + bytes(first)).digest()[:16]
        return generic.ArrayObject([first, generic.ByteStringObject(digest)])


def _writer(data: bytes, modified: datetime = PINNED_EDIT_TIME) -> _Writer:
    return _Writer(io.BytesIO(data), modified)


class _FixedTimeSigner(PdfSigner):
    def __init__(self, *args: Any, signing_time: datetime, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._signing_time = signing_time

    def init_signing_session(self, *args: Any, **kwargs: Any) -> Any:
        session = super().init_signing_session(*args, **kwargs)
        session.system_time = self._signing_time
        return session


def asn1_cert(cert: Any) -> asn1_x509.Certificate:
    return asn1_x509.Certificate.load(cert.public_bytes(serialization.Encoding.DER))


def sign(
    data: bytes,
    identity: pki.Identity,
    field_name: str,
    signing_time: datetime,
    *,
    reason: str | None = None,
    location: str | None = None,
    visible: tuple[int, tuple[float, float, float, float]] | None = None,
) -> bytes:
    """Append a real CMS signature (/ByteRange) by `identity` at `signing_time`.

    `visible` = (0-based page, (x0, y0, x1, y1)) places a visible signature widget there.
    """
    key = asn1_keys.PrivateKeyInfo.load(
        identity.key.private_bytes(
            serialization.Encoding.DER,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    chain = [] if identity.cert.issuer == identity.cert.subject else [pki.intermediate().cert]
    signer = signers.SimpleSigner(
        signing_cert=asn1_cert(identity.cert),
        signing_key=key,
        cert_registry=SimpleCertificateStore.from_certs([asn1_cert(c) for c in chain]),
    )
    meta = signers.PdfSignatureMetadata(
        field_name=field_name, md_algorithm="sha512", reason=reason, location=location
    )
    spec = None
    if visible is not None:
        page, box = visible
        x0, y0, x1, y1 = (round(v) for v in box)
        spec = fields.SigFieldSpec(sig_field_name=field_name, on_page=page, box=(x0, y0, x1, y1))
    pdf_signer = _FixedTimeSigner(meta, signer, signing_time=signing_time, new_field_spec=spec)
    out = pdf_signer.sign_pdf(_writer(data, signing_time))
    return bytes(out.getvalue())


def add_page_content(data: bytes, page: int, text: str) -> bytes:
    """A disallowed change after signing: new content drawn on a page in an incremental update."""
    w = _writer(data)
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = generic.StreamObject(
        stream_data=f"BT /F1 9 Tf 72 90 Td ({escaped}) Tj ET".encode("latin-1")
    )
    w.add_stream_to_page(page, w.add_object(stream))
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def add_dss(data: bytes, crl_der: bytes) -> bytes:
    """A benign change after signing: validation data (DSS: certs + CRL) for long-term checks."""
    w = _writer(data)
    certs = [asn1_cert(pki.intermediate().cert), asn1_cert(pki.trust_anchor().cert)]
    DocumentSecurityStore.supply_dss_in_writer(
        w, None, certs=certs, crls=[asn1_crl.CertificateList.load(crl_der)]
    )
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def touch_info(data: bytes, producer: str) -> bytes:
    """A benign change after signing: only the document information dictionary changes."""
    w = _writer(data)
    ref = w.trailer.raw_get("/Info")
    info = ref.get_object()
    info[generic.NameObject("/Producer")] = generic.TextStringObject(producer)
    w.mark_update(ref)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def flip_signed_byte(data: bytes, marker: bytes = b"SYNTHETIC Affidavit 2") -> bytes:
    """Change one byte inside the first signed byte range (the document title), same length."""
    index = data.index(marker) + len(marker) - 1
    replacement = b"3" if data[index : index + 1] != b"3" else b"4"
    return data[:index] + replacement + data[index + 1 :]
