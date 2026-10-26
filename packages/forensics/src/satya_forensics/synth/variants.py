"""M6 / P-18 planted anomalies and clean controls (docs/SYNTHETIC-TESTSET-PLAN.md §5.2).

Each case is the slice-1 synthetic Affidavit 2 (clean M5 content) plus what M6 looks at: real
pyHanko signatures from the test PKI, a printed "Digitally signed by …" mark, edits after signing,
the e-stamp page, the notary block and a one-page audited statement with a UDIN. The generator
writes down what it planted (`truth-m6.json`); the engine never reads it.

About a third of the variants are "noisy but clean" controls (benign incremental updates, odd
signature metadata, a certificate with one day left, a CRL entry dated after signing, same-day
dates, dates that only parse one way, a visible real signature, a UDIN printed with spaces), so the
false-flag rate is measured on documents that look suspicious but are not.
"""

import random
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, time, timedelta, timezone
from typing import Any

from satya_affidavit.ids import sha256_hex, stable_id
from satya_affidavit.synth.institutions import PROFILES, institution
from satya_affidavit.synth.render import PrintModel
from satya_affidavit.synth.variants import GeneratedCase, Hooks, generate
from satya_forensics import pki
from satya_forensics.synth import signing
from satya_forensics.synth.accounts import AuditedAccounts, fy_end, render_accounts

IST = timezone(timedelta(hours=5, minutes=30), "IST")
AFFIDAVIT_FILE = "affidavit-sworn.pdf"
ACCOUNTS_FILE = "audited-accounts.pdf"
AFFIDAVIT_SLOT = "annex2.1(i) affidavit"
ACCOUNTS_SLOT = "annex2.1(vii) audited accounts"
UDIN_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"

PLANTED = (
    "sig_digest",
    "sig_modified",
    "sig_revoked",
    "sig_expired",
    "sig_not_yet_valid",
    "sig_untrusted",
    "sig_image_only",
    "sig_signer",
    "sig_revocation_down",
    "uploader_missing",
    "chrono_stamp_after_notary",
    "chrono_dsc_before_notary",
    "chrono_mark_after_notary",
    "stamp_party",
    "stamp_duty",
    "stamp_physical",
    "stamp_reused",
    "notary_expired",
    "udin_length",
    "udin_member",
    "udin_year",
    "udin_reused",
)
CONTROLS = (
    "clean",
    "clean_benign_dss",
    "clean_benign_info",
    "clean_odd_metadata",
    "clean_revoked_late",
    "clean_cert_edge",
    "clean_visible_sig",
    "clean_same_day",
    "clean_ambiguous_dates",
    "clean_udin_spaced",
)
VARIANTS = (*CONTROLS, *PLANTED)


@dataclass(frozen=True)
class Expect:
    """One planted finding: the rule, its check_ref key, the document and the check it drives."""

    rule_id: str
    key: str
    doc: str  # "affidavit" | "accounts"
    kind: str | None  # VerificationResult check kind; None for a flag without a check
    outcome: str
    reason_code: str

    @property
    def check_ref(self) -> str:
        return f"m6:{self.rule_id}:{self.key}"


@dataclass
class Timeline:
    application: date
    stamp_issued: datetime
    notarised: date
    issuer_dsc: datetime
    uploader_dsc: datetime
    uploaded: datetime
    mark: datetime | None = None


@dataclass
class Plan:
    issuer: str | None = "chairman"  # test signer kind, or None = no real issuer signature
    uploader: str | None = "chairman"
    mark: bool = False  # printed "Digitally signed by" mark (no /ByteRange)
    mark_days_after_notary: int = 0
    issuer_visible_over_mark: bool = False
    after_issuer: str | None = None  # "content" (disallowed) | "info" (benign)
    after_uploader: str | None = None  # "dss" (benign)
    flip_byte: bool = False
    odd_metadata: bool = False
    stamp: dict[str, Any] = field(default_factory=dict)
    timeline: Callable[[Timeline], Timeline] | None = None
    application_day: int | None = None  # force the application date's day of month
    udin: str = "valid"  # valid | none | short | member | year | reused | spaced
    frn_digits: int = 6
    expect: list[Expect] = field(default_factory=list)


def _sig(rule: str, role: str, outcome: str, code: str) -> Expect:
    return Expect(rule, role, "affidavit", f"{role}_signature", outcome, code)


def plan_for(variant: str) -> Plan:
    p = Plan()
    match variant:
        case "clean":
            pass
        case "clean_benign_dss":
            p.after_uploader = "dss"
        case "clean_benign_info":
            p.after_issuer = "info"
        case "clean_odd_metadata":
            p.issuer = "secretary"
            p.odd_metadata = True
            p.frn_digits = 7
        case "clean_revoked_late":
            p.issuer = "revoked-late"
        case "clean_cert_edge":
            p.issuer = "edge"
        case "clean_visible_sig":
            p.mark = True
            p.issuer_visible_over_mark = True
        case "clean_same_day":
            p.timeline = _same_day
        case "clean_ambiguous_dates":
            p.application_day = 3
        case "clean_udin_spaced":
            p.udin = "spaced"
            p.frn_digits = 7
        case "sig_digest":
            p.flip_byte = True
            p.expect = [
                _sig("SIG-DIGEST", "issuer", "mismatch_detected", "SIG_DIGEST_MISMATCH"),
                _sig("SIG-DIGEST", "uploader", "mismatch_detected", "SIG_DIGEST_MISMATCH"),
            ]
        case "sig_modified":
            p.after_issuer = "content"
            p.expect = [
                _sig("SIG-MODIFIED", "issuer", "mismatch_detected", "SIG_MODIFIED_AFTER_SIGNING")
            ]
        case "sig_revoked":
            p.issuer = "revoked"
            p.expect = [_sig("SIG-REVOKED", "issuer", "mismatch_detected", "SIG_CERT_REVOKED")]
        case "sig_expired":
            p.issuer = "expired"
            p.expect = [_sig("SIG-CERT-EXPIRED", "issuer", "expired", "SIG_CERT_EXPIRED")]
        case "sig_not_yet_valid":
            p.issuer = "not-yet-valid"
            p.expect = [_sig("SIG-CERT-EXPIRED", "issuer", "expired", "SIG_CERT_EXPIRED")]
        case "sig_untrusted":
            p.issuer = "untrusted"
            p.expect = [
                _sig("SIG-UNTRUSTED", "issuer", "manual_review_required", "SIG_UNTRUSTED_CHAIN")
            ]
        case "sig_image_only":
            p.issuer, p.mark = None, True
            p.expect = [_sig("SIG-IMAGE", "issuer", "manual_review_required", "SIG_IMAGE_ONLY")]
        case "sig_signer":
            p.issuer = "wrong-signer"
            p.expect = [
                _sig("SIG-SIGNER", "issuer", "manual_review_required", "SIG_SIGNER_NOT_MATCHED")
            ]
        case "sig_revocation_down":
            p.issuer = "crl-down"
            p.expect = [
                _sig(
                    "SIG-REVOCATION",
                    "issuer",
                    "source_unavailable",
                    "SIG_REVOCATION_UNREACHABLE",
                )
            ]
        case "uploader_missing":
            p.uploader = None
            p.expect = [
                Expect(
                    "SIG-UPLOADER-MISSING",
                    "uploader",
                    "affidavit",
                    None,
                    "manual_review_required",
                    "UPLOADER_DSC_MISSING",
                )
            ]
        case "chrono_stamp_after_notary":
            p.timeline = _stamp_after_notary
            p.expect = [_chrono("order", "CHRONO_ORDER_BROKEN")]
        case "chrono_dsc_before_notary":
            p.timeline = _dsc_before_notary
            p.expect = [_chrono("order", "CHRONO_ORDER_BROKEN")]
        case "chrono_mark_after_notary":
            p.issuer, p.mark, p.mark_days_after_notary = None, True, 2
            p.expect = [
                _sig("SIG-IMAGE", "issuer", "manual_review_required", "SIG_IMAGE_ONLY"),
                _chrono("mark_after_notary", "CHRONO_MARK_AFTER_NOTARISATION"),
            ]
        case "stamp_party":
            p.stamp = {"second_party": "DEMO EDUCATIONAL TRUST OFFICE"}
            p.expect = [
                _fmt(
                    "STAMP-PARTY",
                    "stamp:second_party",
                    "mismatch_detected",
                    "STAMP_PARTY_NOT_COUNCIL",
                )
            ]
        case "stamp_duty":
            p.stamp = {"duty": 50}
            p.expect = [
                _fmt("STAMP-DUTY", "stamp:duty", "mismatch_detected", "STAMP_DUTY_BELOW_100")
            ]
        case "stamp_physical":
            p.stamp = {"instrument": "physical"}
            p.expect = [
                _fmt(
                    "STAMP-INSTRUMENT",
                    "stamp:instrument",
                    "manual_review_required",
                    "STAMP_NOT_E_STAMP",
                )
            ]
        case "stamp_reused":
            p.stamp = {"reuse_prior_year": True}
            p.expect = [
                _fmt(
                    "STAMP-REUSE",
                    "stamp:certificate_no",
                    "manual_review_required",
                    "STAMP_NO_REUSED",
                )
            ]
        case "notary_expired":
            p.stamp = {"notary_expired": True}
            p.expect = [
                Expect(
                    "NOTARY-EXPIRY",
                    "notary:seal_expiry",
                    "affidavit",
                    "expiry",
                    "expired",
                    "NOTARY_SEAL_EXPIRED",
                )
            ]
        case "udin_length":
            p.udin = "short"
            p.expect = [_udin("UDIN-STRUCT", "udin:format", "UDIN_MALFORMED")]
        case "udin_member":
            p.udin = "member"
            p.expect = [_udin("UDIN-MEMBER", "udin:membership_no", "UDIN_MEMBER_MISMATCH")]
        case "udin_year":
            p.udin = "year"
            p.expect = [_udin("UDIN-STRUCT", "udin:year", "UDIN_YEAR_BEFORE_FY_END")]
        case "udin_reused":
            p.udin = "reused"
            p.expect = [_udin("UDIN-REUSE", "udin:reuse", "UDIN_REUSED")]
        case _:
            raise KeyError(f"unknown M6 variant {variant}")
    return p


def _chrono(key: str, code: str) -> Expect:
    return Expect(
        "STAMP-CHRONO",
        f"chronology:{key}",
        "affidavit",
        "chronology",
        "manual_review_required",
        code,
    )


def _fmt(rule: str, key: str, outcome: str, code: str) -> Expect:
    return Expect(rule, key, "affidavit", "format", outcome, code)


def _udin(rule: str, key: str, code: str) -> Expect:
    return Expect(rule, key, "accounts", "format", "manual_review_required", code)


def _at(day: date, hh: int, mm: int) -> datetime:
    return datetime.combine(day, time(hh, mm), IST)


def base_timeline(application: date) -> Timeline:
    """Application → stamp (+1) → notarisation (+2) → issuer DSC (+3) → upload (+3) (design D1)."""
    d3 = application + timedelta(days=3)
    return Timeline(
        application=application,
        stamp_issued=_at(application + timedelta(days=1), 11, 5),
        notarised=application + timedelta(days=2),
        issuer_dsc=_at(d3, 10, 15),
        uploader_dsc=_at(d3, 16, 30),
        uploaded=_at(d3, 16, 40),
    )


def _same_day(t: Timeline) -> Timeline:
    d = t.application
    return replace(
        t,
        stamp_issued=_at(d, 9, 30),
        notarised=d,
        issuer_dsc=_at(d, 15, 0),
        uploader_dsc=_at(d, 16, 30),
        uploaded=_at(d, 16, 45),
    )


def _stamp_after_notary(t: Timeline) -> Timeline:
    return replace(t, stamp_issued=_at(t.notarised + timedelta(days=1), 9, 0))


def _dsc_before_notary(t: Timeline) -> Timeline:
    return replace(t, issuer_dsc=_at(t.notarised - timedelta(days=1), 15, 0))


# ---- shared synthetic registers (prior filings) --------------------------------------------------
def membership_no(profile: int) -> str:
    return f"99{profile:02d}{(profile * 7) % 100:02d}"


def frn(profile: int, digits: int) -> str:
    core = f"99{profile:02d}03"
    return f"{'0' if digits == 7 else ''}{core}S"


def make_udin(profile: int, fy: str, membership: str, salt: str = "") -> str:
    rng = random.Random(f"satya-udin-{profile}-{fy}-{salt}")
    yy = f"{fy_end(fy).year % 100:02d}"
    letters = "".join(rng.choice(UDIN_LETTERS) for _ in range(6))
    return f"{yy}{membership}{letters}{rng.randint(1000, 9999)}"


def previous_fy(ay: str) -> str:
    start = int(ay[:4])
    return f"{start - 1}-{str(start)[2:]}"


def prior_filings() -> dict[str, Any]:
    """Synthetic register of earlier filings that M6 checks reuse against (within the corpus).

    stamps: each profile's 2025-26 e-stamp certificate. udins: each profile's FY 2024-25 UDIN, and
    a FY 2025-26 UDIN of a sister filing audited by the same partner (other permanent ID).
    """
    stamps, udins = [], []
    for profile in sorted(PROFILES):
        prev = institution(profile, "2025-26").case
        stamps.append(
            {
                "certificate_no": prev["stamp"]["certificate_no"],
                "application_id": prev["application_id"],
                "ay": "2025-26",
            }
        )
        member = membership_no(profile)
        udins.append(
            {
                "udin": make_udin(profile, "2024-25", member),
                "permanent_id": prev["permanent_id"],
                "fy": "2024-25",
            }
        )
        udins.append(
            {
                "udin": make_udin(profile, "2025-26", member, "sister"),
                "permanent_id": f"1-90099{profile:02d}",
                "fy": "2025-26",
            }
        )
    return {
        "_synthetic": "SYNTHETIC register of earlier filings for the M6 reuse checks.",
        "stamps": stamps,
        "udins": udins,
    }


# ---- case assembly ---------------------------------------------------------------------------
@dataclass(frozen=True)
class M6Case:
    slug: str
    variant: str
    profile: int
    case: dict[str, Any]
    snapshot: dict[str, Any]
    files: dict[str, bytes]  # file name -> bytes
    truth: dict[str, Any]
    m5_truth: dict[str, Any]
    crl_specs: tuple[pki.SignerSpec, ...]


def _mark_lines(name: str, when: datetime) -> list[str]:
    return [
        f"Digitally signed by {name}",
        f"Date: {when:%Y.%m.%d %H:%M:%S} +05'30'",
        "Signature valid",
    ]


def _udin_for(plan: Plan, profile: int, fy: str, member: str) -> tuple[str | None, str]:
    """(UDIN as printed, membership no. as printed)."""
    valid = make_udin(profile, fy, member)
    match plan.udin:
        case "none":
            return None, member
        case "short":
            return valid[:-5] + valid[-4:], member
        case "member":
            other = f"{int(member) + 11:06d}"
            return valid[:2] + other + valid[8:], member
        case "year":
            return f"{int(valid[:2]) - 1:02d}" + valid[2:], member
        case "reused":
            return make_udin(profile, fy, member, "sister"), member
        case "spaced":
            return f"{valid[:2]} {valid[2:8]} {valid[8:14]} {valid[14:]}", member
    return valid, member


def build_case(
    profile: int, variant: str, *, demo: bool = False, m5_variant: str = "clean"
) -> M6Case:
    """One synthetic case with a signed affidavit and an audited statement, plus M6 truth."""
    plan = plan_for(variant)
    if demo:
        # Demo story F5/F6/F10: page mark is an image dated two days after notarisation, the
        # uploader DSC chains to the TEST TRUST ANCHOR, the audited statement has no UDIN.
        plan = Plan(
            issuer=None,
            mark=True,
            mark_days_after_notary=2,
            udin="none",
            expect=plan_for("chrono_mark_after_notary").expect,
        )
    rng = random.Random(f"satya-m6-{profile}-{variant}")
    holder: dict[str, Any] = {}

    def on_case(case: dict[str, Any], snapshot: dict[str, Any]) -> None:
        basic = snapshot["basic"]
        application = date.fromisoformat(basic["application_date"])
        if plan.application_day is not None:
            application = application.replace(day=plan.application_day)
            basic["application_date"] = application.isoformat()
            basic["submission_date"] = (application + timedelta(days=4)).isoformat()
            snapshot["captured_at"] = f"{application.isoformat()}T11:05:00+05:30"
        t = base_timeline(application)
        if plan.timeline:
            t = plan.timeline(t)
        if plan.mark and plan.issuer_visible_over_mark:
            t.mark = t.issuer_dsc  # the appearance of the real signature carries its own time
        elif plan.mark:
            mark_day = t.notarised + timedelta(days=plan.mark_days_after_notary)
            t.mark = _at(mark_day, 10, 15)
            if t.mark > t.issuer_dsc:
                t.issuer_dsc = t.mark
            if t.mark.date() >= t.uploaded.date():
                t.uploader_dsc = _at(mark_day, 16, 30)
                t.uploaded = _at(mark_day, 16, 40)
                basic["submission_date"] = (mark_day + timedelta(days=1)).isoformat()
        stamp = case["stamp"]
        stamp["issued"] = t.stamp_issued.replace(tzinfo=None).isoformat(timespec="minutes")
        stamp["notarised"] = t.notarised.isoformat()
        for key in ("second_party", "duty", "instrument"):
            if key in plan.stamp:
                stamp[key] = plan.stamp[key]
        if plan.stamp.get("instrument") == "physical":
            stamp["certificate_no"] = f"DEMO-NJ-9{profile:02d}{4217 + profile:05d}"
        if plan.stamp.get("reuse_prior_year"):
            stamp["certificate_no"] = institution(profile, "2025-26").case["stamp"][
                "certificate_no"
            ]
        if plan.stamp.get("notary_expired"):
            stamp["notary_valid_till"] = (t.notarised - timedelta(days=10)).isoformat()
        holder["timeline"] = t
        holder["signatory"] = snapshot["authorised_signatory"]["name"]

    def on_model(model: PrintModel) -> None:
        t: Timeline = holder["timeline"]
        if plan.mark and t.mark is not None:
            model.dsc_mark = _mark_lines(holder["signatory"], t.mark)

    hooks = Hooks(case=on_case, model=on_model)
    m5_name = "clean" if demo else m5_variant
    generated: GeneratedCase = generate(profile, m5_name, demo=demo, hooks=hooks)
    t = holder["timeline"]
    signatory = holder["signatory"]
    case = generated.case
    specs: list[pki.SignerSpec] = []

    def identity(kind: str, when: datetime) -> pki.Identity:
        spec = pki.signer_spec(kind, profile, signatory, when.astimezone(UTC))
        if plan.odd_metadata and kind in ("chairman", "secretary"):
            spec = replace(spec, common_name=f"  {signatory.upper()}  ")
        specs.append(spec)
        return pki.signer(spec)

    pdf = generated.pdf
    if plan.issuer is not None:
        visible = None
        if plan.issuer_visible_over_mark and generated.mark_box is not None:
            page, x0, y0, x1, y1 = generated.mark_box
            visible = (page - 1, (x0, y0, x1, y1))
        reason = "  " if plan.odd_metadata else "I am the deponent of this affidavit"
        location = (
            "Démo Town / ✓" if plan.odd_metadata else case["affidavit_draft"]["header"]["town"]
        )
        pdf = signing.sign(
            pdf,
            identity(plan.issuer, t.issuer_dsc),
            "Signature1" if plan.odd_metadata else "DeponentSignature",
            t.issuer_dsc,
            reason=reason,
            location=location,
            visible=visible,
        )
    if plan.after_issuer == "content":
        last = max(generated.positions.values()) - 1
        pdf = signing.add_page_content(pdf, last, "Land area amended to 9.99 acre (SYNTHETIC EDIT)")
    elif plan.after_issuer == "info":
        pdf = signing.touch_info(pdf, "Demo PDF Toolkit 0.0 (synthetic)")
    if plan.uploader is not None:
        pdf = signing.sign(
            pdf,
            identity(plan.uploader, t.uploader_dsc),
            "UploaderSignature",
            t.uploader_dsc,
            reason="Uploaded to the approval portal (mock)",
        )
    if plan.after_uploader == "dss":
        pdf = signing.add_dss(pdf, pki.build_crl({}))
    if plan.flip_byte:
        pdf = signing.flip_signed_byte(pdf)

    # Audited statement (P-18): signed by the uploader's DSC; the CA's own signature is wet.
    fy = previous_fy(case["ay"])
    member = membership_no(profile)
    udin, printed_member = _udin_for(plan, profile, fy, member)
    report_day = date(fy_end(fy).year, 9, 10 + rng.randint(0, 15))
    accounts = AuditedAccounts(
        application_id=case["application_id"],
        trust_name=generated.snapshot["trust"]["name"],
        institution_name=case["institution_name"],
        town=case["affidavit_draft"]["header"]["town"],
        fy=fy,
        income_rupees=48_000_000 + profile * 1_000_000,
        expenditure_rupees=41_000_000 + profile * 900_000,
        firm=f"Demo and Associates {profile:02d} (synthetic)",
        frn=frn(profile, plan.frn_digits),
        partner=f"Demo Auditor {profile:02d}",
        membership_no=printed_member,
        udin=udin,
        report_date=report_day,
    )
    accounts_pdf = signing.sign(
        render_accounts(accounts),
        identity("chairman", t.uploader_dsc),
        "UploaderSignature",
        t.uploader_dsc,
        reason="Uploaded to the approval portal (mock)",
    )

    files = {AFFIDAVIT_FILE: pdf, ACCOUNTS_FILE: accounts_pdf}
    uploaded = t.uploaded.isoformat()
    case["documents"] = [
        _document(
            AFFIDAVIT_FILE,
            pdf,
            AFFIDAVIT_SLOT,
            "affidavit-2",
            "Affidavit 2 (sworn copy)",
            "T",
            uploaded,
        ),
        _document(
            ACCOUNTS_FILE,
            accounts_pdf,
            ACCOUNTS_SLOT,
            "audited-accounts",
            f"Audited statement of accounts FY {fy}",
            "E",
            uploaded,
        ),
    ]
    doc_ids = {
        "affidavit": case["documents"][0]["doc_id"],
        "accounts": case["documents"][1]["doc_id"],
    }
    name = "demo" if demo else variant
    slug = f"{case['case_id'][-4:].lower()}-{case['ay']}-m6-{name}"
    truth = {
        "_synthetic": case["_synthetic"],
        "case": slug,
        "profile": profile,
        "variant": name,
        "control": variant in CONTROLS and not demo,
        "timeline": {
            "application": t.application.isoformat(),
            "stamp_issued": t.stamp_issued.isoformat(),
            "notarised": t.notarised.isoformat(),
            "issuer_dsc": t.issuer_dsc.isoformat() if plan.issuer else None,
            "mark": t.mark.isoformat() if t.mark else None,
            "uploader_dsc": t.uploader_dsc.isoformat() if plan.uploader else None,
            "uploaded": uploaded,
        },
        "expected_flags": [
            {
                "rule_id": e.rule_id,
                "check_ref": e.check_ref,
                "doc_id": doc_ids[e.doc],
                "label": e.outcome,
            }
            for e in plan.expect
        ],
        "expected_checks": [
            {
                "doc_id": doc_ids[e.doc],
                "kind": e.kind,
                "outcome": e.outcome,
                "reason_code": e.reason_code,
            }
            for e in plan.expect
            if e.kind is not None
        ],
        "expected_document_labels": {
            doc_ids["affidavit"]: _expected_label(plan, "affidavit", "verified"),
            doc_ids["accounts"]: _expected_label(plan, "accounts", "source_unavailable"),
        },
        "printed": {
            "stamp.certificate_no": case["stamp"]["certificate_no"],
            "stamp.second_party": case["stamp"].get("second_party"),
            "stamp.duty": case["stamp"].get("duty"),
            "stamp.issued": t.stamp_issued.date().isoformat(),
            "notary.date": t.notarised.isoformat(),
            "notary.valid_till": case["stamp"]["notary_valid_till"],
            "mark.date": t.mark.date().isoformat() if t.mark else None,
            "udin": None if udin is None else "".join(udin.split()),
            "udin.membership_no": printed_member,
        },
    }
    return M6Case(
        slug=slug,
        variant=name,
        profile=profile,
        case=case,
        snapshot=generated.snapshot,
        files=files,
        truth=truth,
        m5_truth=generated.truth,
        crl_specs=tuple(specs),
    )


PRECEDENCE = (
    "mismatch_detected",
    "expired",
    "manual_review_required",
    "source_unavailable",
    "verification_pending",
    "verified",
)


def _expected_label(plan: Plan, doc: str, baseline: str) -> str:
    outcomes = [e.outcome for e in plan.expect if e.doc == doc and e.kind is not None]
    return min([baseline, *outcomes], key=PRECEDENCE.index)


def _document(
    file: str, data: bytes, slot: str, declared: str, title: str, fmt: str, uploaded: str
) -> dict[str, Any]:
    digest = sha256_hex(data)
    return {
        "doc_id": stable_id("doc", digest),
        "slot": slot,
        "declared_type": declared,
        "title": title,
        "format_type": fmt,
        "file": file,
        "sha256": digest,
        "bytes": len(data),
        "uploaded_at": uploaded,
    }
