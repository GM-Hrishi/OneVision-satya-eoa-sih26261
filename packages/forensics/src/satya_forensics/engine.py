"""M6 engine: a case's documents → VerificationResult per document (Portal spec §2.7), the two
signature badges (UI §4.3), the affidavit's stamp and signing-order section (UI §6.3) and Flags.

Deterministic and side-effect free apart from the revocation fetches it is given: the same bytes,
snapshot, registry and CRLs give the same JSON (Portal §2.11). Advisory only: nothing here
approves, rejects or clears anything, and a valid uploader signature never makes a document
verified (Portal §2.6.3).
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from satya_affidavit.ids import sha256_hex, token
from satya_affidavit.template import load_template
from satya_forensics.flags import FlagFactory
from satya_forensics.labels import document_label, most_severe
from satya_forensics.registry import Registry
from satya_forensics.rules import Ruleset, load_ruleset
from satya_forensics.signatures import (
    RevocationSource,
    SignatureContext,
    SigResult,
    TrustStore,
    inspect,
    issuer_not_digital,
    signature_check,
)
from satya_forensics.stamp import Finding
from satya_forensics.stamp import evaluate as evaluate_stamp
from satya_forensics.textlayer import Page, find_marks, read_pages
from satya_forensics.udin import evaluate as evaluate_udin
from satya_forensics.udin import read_accounts
from satya_forensics.udin import source_check as udin_source_check
from satya_ocr.model import DocumentRead

ENGINE_VERSION = "0.1.0"
AFFIDAVIT_SLOT = "annex2.1(i) affidavit"
ACCOUNTS_SLOT = "annex2.1(vii) audited accounts"
SIGNATURE_CONFIDENCE = 0.99
MARK_CONFIDENCE = 0.9


@dataclass(frozen=True)
class M6Input:
    case: dict[str, Any]  # case metadata incl. documents[] (doc_id, slot, title, uploaded_at, …)
    snapshot: dict[str, Any]
    files: dict[str, bytes]  # doc_id -> bytes (already hash-checked by the caller)
    token_key: bytes
    trust: TrustStore
    revocation: RevocationSource
    registry: Registry
    checked_at: str  # RFC 3339; when this run happened
    reads: dict[str, DocumentRead] | None = None  # doc_id -> satya_ocr read (scans, unreadable)
    ruleset: Ruleset | None = None  # replay (P-11): an archived rule pack; default = current


@dataclass
class DocumentResult:
    doc_id: str
    slot: str
    title: str
    format_type: str
    verification: dict[str, Any]
    issuer_sig: dict[str, Any] | None
    uploader_sig: dict[str, Any] | None
    source: dict[str, str]
    response_ref: str | None
    flags: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class M6Result:
    documents: list[DocumentResult]
    affidavit: dict[str, Any] | None  # stamp, chronology, issuer_sig, uploader_sig for RB-05
    flags: list[dict[str, Any]]
    engine_version: str = ENGINE_VERSION
    ruleset_version: str = ""


def scan_check(read: DocumentRead) -> dict[str, Any]:
    """The one check a scan or an unreadable file gets from M3: always manual review."""
    return {
        "kind": "format",
        "outcome": "manual_review_required",
        "reason_code": read.reason_code or "SCAN_IMAGE_ONLY",
        "check_ref": f"m3:OCR-READ:{read.variant}",
    }


def _blocked_result(doc: dict[str, Any], read: DocumentRead) -> DocumentResult:
    """Nothing can be decided safely: no signature or text checks are run on the file."""
    return DocumentResult(
        doc_id=doc["doc_id"],
        slot=doc["slot"],
        title=doc.get("title", doc["slot"]),
        format_type=doc.get("format_type", "E"),
        verification={
            "doc_id": doc["doc_id"],
            "label": "manual_review_required",
            "decided_by": "system",
            "checks": [scan_check(read)],
        },
        issuer_sig=None,
        uploader_sig=None,
        source={"channel": "pdf-signature", "adapter_mode": "offline"},
        response_ref=None,
    )


def signatory_token(snapshot: dict[str, Any], key: bytes) -> str | None:
    signatory = snapshot.get("authorised_signatory") or {}
    if signatory.get("signatory_token"):
        return str(signatory["signatory_token"])
    name = signatory.get("name")
    return token(key, name) if name else None


def _evidence(result: SigResult) -> dict[str, Any] | None:
    if result.page is None:
        return None
    return {"page": result.page, "regions": result.regions}


def _signature_items(
    result: SigResult,
    factory: FlagFactory,
    ruleset: Ruleset,
    trust_label: str,
    *,
    emit_check: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(checks, flags) for one signature result."""
    checks: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = []
    rule = None
    if result.reason_code not in ("SIG_VALID", "SIG_NOT_DIGITAL"):
        rule = ruleset.by_reason(result.reason_code)
    check_ref = f"m6:{rule.rule_id}:{result.role}" if rule else None
    if result.present and emit_check and result.outcome is not None:
        check: dict[str, Any] = {
            "kind": f"{result.role}_signature",
            "outcome": result.outcome,
            "reason_code": result.reason_code,
        }
        evidence = _evidence(result)
        if evidence:
            check["evidence"] = evidence
        if result.signed_at is not None and result.has_byte_range:
            check["signed_at"] = result.signed_at.isoformat()
        if result.trust_anchor_label:
            check["trust_anchor_label"] = result.trust_anchor_label
        if result.revocation_attempts:
            check["attempts"] = result.revocation_attempts
        if check_ref:
            check["check_ref"] = check_ref
        checks.append(check)
    if rule is not None:
        expected = {
            "SIG-IMAGE": "real CMS signature (/ByteRange) chaining to the trust anchor",
            "SIG-SIGNER": "authorised Chairman/Secretary (signatory token)",
            "SIG-UNTRUSTED": "chain to the trust anchor",
            "SIG-CERT-EXPIRED": "certificate valid at the signing time",
            "SIG-UPLOADER-MISSING": "institution's DSC on the uploaded file (2.3.4a)",
            "SIG-REVOCATION": "CRL of the issuing CA reachable",
        }.get(rule.rule_id, "signature intact, unmodified and unrevoked")
        extracted = result.extracted if result.extracted is not None else result.reason_code
        flags.append(
            factory.make(
                rule.rule_id,
                result.role,
                page=result.page,
                regions=result.regions,
                extracted=extracted,
                expected=expected,
                expected_label="Portal spec §2.8 signature rules",
                confidence=MARK_CONFIDENCE if not result.has_byte_range else SIGNATURE_CONFIDENCE,
            )
        )
    return checks, flags


@dataclass
class DocContext:
    doc: dict[str, Any]
    pdf: bytes
    pages: list[Page]
    factory: FlagFactory
    issuer: SigResult
    uploader: SigResult
    checks: list[dict[str, Any]] = field(default_factory=list)
    flags: list[dict[str, Any]] = field(default_factory=list)


def run(inp: M6Input) -> M6Result:
    ruleset = inp.ruleset or load_ruleset()
    sig_ctx = SignatureContext(
        trust=inp.trust,
        revocation=inp.revocation,
        token_key=inp.token_key,
        signatory_token=signatory_token(inp.snapshot, inp.token_key),
        retries=ruleset["SIG-REVOCATION"].retries,
    )
    documents: list[DocumentResult] = []
    affidavit_section: dict[str, Any] | None = None
    all_flags: list[dict[str, Any]] = []
    for doc in inp.case.get("documents", []):
        pdf = inp.files.get(doc["doc_id"])
        if pdf is None:
            continue
        read = inp.reads.get(doc["doc_id"]) if inp.reads else None
        if read is not None and read.blocked:
            documents.append(_blocked_result(doc, read))
            continue
        pages = read_pages(pdf, read.layers() if read else None)
        slot = doc["slot"]
        report = inspect(
            pdf, pages, find_marks(pages), sig_ctx, external=doc.get("format_type") == "E"
        )
        issuer = report.issuer
        if slot != AFFIDAVIT_SLOT and issuer.reason_code == "SIG_NOT_DIGITAL":
            issuer = issuer_not_digital()
        factory = FlagFactory(ruleset, doc["doc_id"], sha256_hex(pdf), doc.get("title", slot))
        ctx = DocContext(doc, pdf, pages, factory, issuer, report.uploader)
        # The affidavit must carry the deponent's DSC (2.3.4b); for external documents the
        # issuer's authenticity comes from a source lookup and a wet seal is not a finding.
        emit_issuer = slot == AFFIDAVIT_SLOT or issuer.reason_code != "SIG_NOT_DIGITAL"
        for result, emit in ((issuer, emit_issuer), (report.uploader, True)):
            checks, flags = _signature_items(
                result, factory, ruleset, inp.trust.label, emit_check=emit
            )
            ctx.checks += checks
            ctx.flags += flags
        if read is not None and read.needs_review:
            ctx.checks.append(scan_check(read))
        if slot == AFFIDAVIT_SLOT:
            affidavit_section = _affidavit(ctx, inp)
        elif slot == ACCOUNTS_SLOT:
            _accounts(ctx, inp)
        source = {"channel": "pdf-signature", "adapter_mode": "offline"}
        lookups = [c for c in ctx.checks if c["kind"] == "source_lookup"]
        if lookups and "source" in lookups[0]:
            src = lookups[0]["source"]
            source = {"channel": src["adapter_id"], "adapter_mode": src["mode"]}
        verification = {
            "doc_id": doc["doc_id"],
            "label": document_label(ctx.checks),
            "decided_by": "system",
            "checks": ctx.checks,
        }
        documents.append(
            DocumentResult(
                doc_id=doc["doc_id"],
                slot=slot,
                title=doc.get("title", slot),
                format_type=doc.get("format_type", "E"),
                verification=verification,
                issuer_sig=signature_check(issuer),
                uploader_sig=signature_check(report.uploader),
                source=source,
                response_ref=None,
                flags=ctx.flags,
            )
        )
        all_flags += ctx.flags
    return M6Result(
        documents=documents,
        affidavit=affidavit_section,
        flags=all_flags,
        ruleset_version=ruleset.ref,
    )


def _date_order(case: dict[str, Any]) -> str:
    template_id = (case.get("affidavit_draft") or {}).get("template_id")
    try:
        return load_template(template_id).date_order if template_id else "MM/DD/YYYY"
    except (FileNotFoundError, KeyError):
        return "MM/DD/YYYY"


def _finding_items(
    finding: Finding, ctx: DocContext, ruleset: Ruleset
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """(check, flag or None) for one stamp/chronology/notary/UDIN finding."""
    rule = ruleset[finding.rule_id]
    sub = finding.key.split(":", 1)[1]
    if finding.failed:
        code = rule.code(sub) if sub in dict(rule.other_codes) else rule.reason_code
    else:
        code = (
            rule.code(f"{sub}_pass") if f"{sub}_pass" in dict(rule.other_codes) else rule.pass_code
        )
    regions: list[dict[str, float]] = list(finding.extra.get("regions", []))
    if finding.box is not None and finding.page is not None:
        regions = [ctx.pages[finding.page - 1].region(finding.box)]
    check: dict[str, Any] = {
        "kind": finding.kind,
        "outcome": rule.label if finding.failed else "verified",
        "reason_code": code,
    }
    if finding.page is not None:
        check["evidence"] = {"page": finding.page, "regions": regions}
    if "valid_to" in finding.extra:
        check["valid_to"] = finding.extra["valid_to"]
        check["basis"] = finding.extra["basis"]
    flag = None
    if finding.failed:
        check["check_ref"] = f"m6:{rule.rule_id}:{finding.key}"
        flag = ctx.factory.make(
            rule.rule_id,
            finding.key,
            page=finding.page,
            regions=regions,
            extracted=finding.extracted,
            expected=finding.expected,
            expected_label=f"{rule.aph_clause} ({ruleset.name})",
            confidence=finding.confidence,
        )
    return check, flag


STAMP_RULES = ("STAMP-INSTRUMENT", "STAMP-PARTY", "STAMP-DUTY", "STAMP-REUSE")


def _affidavit(ctx: DocContext, inp: M6Input) -> dict[str, Any]:
    """Stamp page, notary block and signing order (UI §6.3 stamp + chronology)."""
    ruleset = inp.ruleset or load_ruleset()
    basic = inp.snapshot.get("basic") or {}
    application = basic.get("application_date")
    uploaded = ctx.doc.get("uploaded_at")
    result = evaluate_stamp(
        ctx.pages,
        _date_order(inp.case),
        ctx.issuer,
        date.fromisoformat(application) if application else None,
        datetime.fromisoformat(uploaded) if uploaded else None,
        inp.case.get("application_id", ""),
        inp.case.get("ay", ""),
        inp.registry,
    )
    stamp_outcomes = []
    for finding in [*result.findings, *([result.ocr_match] if result.ocr_match else [])]:
        check, flag = _finding_items(finding, ctx, ruleset)
        ctx.checks.append(check)
        if flag:
            ctx.flags.append(flag)
        if finding.rule_id in STAMP_RULES and finding.failed:
            stamp_outcomes.append(check["outcome"])
    if result.stamp is not None:
        # Format checks only; the SHCIL lookup that can verify the stamp is M7 (P-5).
        result.stamp["state"] = most_severe(stamp_outcomes) or "verification_pending"
    return {
        "doc_id": ctx.doc["doc_id"],
        "stamp": result.stamp,
        "chronology": result.chronology,
        "issuer_sig": signature_check(ctx.issuer),
        "uploader_sig": signature_check(ctx.uploader),
    }


def _accounts(ctx: DocContext, inp: M6Input) -> None:
    """P-18 UDIN structure checks and the (unavailable) ICAI lookup on the audited statement."""
    ruleset = inp.ruleset or load_ruleset()
    acc = read_accounts(ctx.pages)
    permanent_id = inp.case.get("permanent_id") or ""
    for finding in evaluate_udin(
        acc, permanent_id, inp.registry, ruleset["UDIN-STRUCT"].max_year_gap
    ):
        check, flag = _finding_items(finding, ctx, ruleset)
        ctx.checks.append(check)
        if flag:
            ctx.flags.append(flag)
    ctx.checks.append(udin_source_check(acc, inp.checked_at))
