# GENERATED from packages/shared-types/schemas by scripts/generate.mjs. Do not edit.

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class SatyaContracts(BaseModel):
    """
    GENERATED from packages/shared-types/schemas by scripts/generate.mjs. Do not edit. All SATYA-EoA contracts (Portal spec §2) in one document.
    """


class AcademicYear(RootModel[str]):
    root: Annotated[str, Field(pattern="^[0-9]{4}-[0-9]{2}$", title="AcademicYear")]
    """
    Academic year as printed, e.g. 2026-27.
    """


class CaseRoute(StrEnum):
    """
    Table 2.3 route (UI spec §6).
    """

    self_disclosure = "self_disclosure"
    scrutiny = "scrutiny"
    scrutiny_evc = "scrutiny_evc"
    scrutiny_only = "scrutiny_only"


class CaseStage(StrEnum):
    """
    C2 stage ①–⑦.
    """

    field_1 = "1"
    field_2 = "2"
    field_3 = "3"
    field_4 = "4"
    field_5 = "5"
    field_6 = "6"
    field_7 = "7"


class TextSource(StrEnum):
    """
    Where the sworn text came from: the PDF text layer, or OCR of a scanned file. Text read by OCR never decides anything.
    """

    text_layer = "text_layer"
    ocr = "ocr"


class DateOrder(StrEnum):
    """
    Date order of the template year (design D4).
    """

    MM_DD_YYYY = "MM/DD/YYYY"
    DD_MM_YYYY = "DD/MM/YYYY"


class AffidavitNormalisation(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    whitespace: bool
    strike_through_resolved: Annotated[int, Field(ge=0)]
    """
    Struck-through spans removed before comparing.
    """
    names_substituted: bool
    hyphens_rejoined: Annotated[int, Field(ge=0)]
    date_order: DateOrder
    """
    Date order of the template year (design D4).
    """
    date_order_fallbacks: Annotated[int | None, Field(ge=0)] = None
    """
    Dates whose month was impossible in the template order and parsed the other way.
    """


class Choice(RootModel[str]):
    root: Annotated[str, Field(max_length=120, min_length=1)]


class SelectedItem(RootModel[str]):
    root: Annotated[str, Field(max_length=120, min_length=1)]


class DeclarationOption(BaseModel):
    """
    A strike-through option group in a declaration and the choice the deponent left standing.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    decl_no: Annotated[int, Field(ge=1)]
    group: Annotated[str, Field(max_length=64, min_length=1)]
    choices: list[Choice]
    selected: list[SelectedItem]


class DiffOpKind(StrEnum):
    equal = "equal"
    added = "added"
    removed = "removed"
    changed = "changed"


class DiffSpanKind(StrEnum):
    equal = "equal"
    insert = "insert"
    delete = "delete"


class DiffSpan(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    kind: Annotated[DiffSpanKind, Field(title="DiffSpanKind")]
    text: Annotated[str, Field(max_length=4000)]


class CategoryLineState(StrEnum):
    present = "present"
    missing = "missing"
    extra = "extra"
    different = "different"


class ExtraBlock(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    heading: Annotated[str, Field(max_length=400, min_length=1)]
    page: Annotated[int, Field(ge=1)]


class AffidavitTableName(StrEnum):
    land = "land"
    room_admin = "room_admin"
    room_amenities = "room_amenities"
    room_instructional = "room_instructional"
    room_common = "room_common"


class Column(RootModel[str]):
    root: Annotated[str, Field(max_length=64, min_length=1)]


class TableRowState(StrEnum):
    matched = "matched"
    differs = "differs"
    missing_in_sworn = "missing_in_sworn"
    extra_in_sworn = "extra_in_sworn"


class SwornCell(RootModel[str | None]):
    root: Annotated[str | None, Field(max_length=400)]


class ApplicationReportCell(RootModel[str | None]):
    root: Annotated[str | None, Field(max_length=400)]


class RoomIdDuplicate(RootModel[str]):
    root: Annotated[str, Field(max_length=64, min_length=1)]


class DscKind(Enum):
    """
    Where dsc_date comes from: a real CMS signature or a printed mark (image only).
    """

    signature = "signature"
    image_mark = "image_mark"
    NoneType_None = None


class ComparisonState(StrEnum):
    compared = "compared"
    not_compared = "not_compared"


class ComparisonSource(StrEnum):
    """
    Where the sworn text came from, or why there is none.
    """

    text_layer = "text_layer"
    scan_read = "scan_read"
    scan_unreliable = "scan_unreliable"
    scan_not_read = "scan_not_read"
    scan_timeout = "scan_timeout"
    ocr_unavailable = "ocr_unavailable"
    unreadable = "unreadable"


class Section(StrEnum):
    stamp = "stamp"
    chronology = "chronology"
    signatures = "signatures"
    ocr = "ocr"


class PendingSection(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    section: Section
    module: Annotated[str, Field(pattern="^M[0-9]{1,2}$")]
    promise: Annotated[str, Field(pattern="^P-[0-9]{1,2}$")]


class AlertId(RootModel[str]):
    root: Annotated[str, Field(pattern="^alr_[0-9A-HJKMNP-TV-Z]{26}$", title="AlertId")]


class AlertSubtype(StrEnum):
    document_missing = "document_missing"
    field_missing = "field_missing"
    category_line_missing = "category_line_missing"
    uploader_dsc_missing = "uploader_dsc_missing"
    document_expired = "document_expired"
    expiring_soon = "expiring_soon"
    partial_oc_limit_reached = "partial_oc_limit_reached"
    signing_cert_expired = "signing_cert_expired"
    source_pending_overdue = "source_pending_overdue"
    source_unavailable = "source_unavailable"
    trust_anchor_revalidation = "trust_anchor_revalidation"
    affidavit_diff = "affidavit_diff"
    signature_integrity = "signature_integrity"
    signature_image_only = "signature_image_only"
    stamp_chronology = "stamp_chronology"
    identity_graph = "identity_graph"
    yoy_discrepancy = "yoy_discrepancy"
    document_misclassified = "document_misclassified"
    media_reuse = "media_reuse"
    flag_undisposed_overdue = "flag_undisposed_overdue"
    manual_task_overdue = "manual_task_overdue"
    clarification_overdue = "clarification_overdue"
    compliance_window_expiring = "compliance_window_expiring"
    compliance_window_lapsed = "compliance_window_lapsed"
    case_assigned = "case_assigned"
    sitting_scheduled = "sitting_scheduled"
    evc_scheduled = "evc_scheduled"
    hearing_scheduled = "hearing_scheduled"
    selection_round_opened = "selection_round_opened"


class AlertType(StrEnum):
    missing_info = "missing_info"
    expired = "expired"
    pending_source = "pending_source"
    suspected_anomaly = "suspected_anomaly"
    unresolved = "unresolved"
    role = "role"


class ApplicationId(RootModel[str]):
    root: Annotated[str, Field(pattern="^1-[0-9]{10,11}$", title="ApplicationId")]
    """
    Portal application ID in printed form (design D4). Demo data uses 1-9….
    """


class TriState(StrEnum):
    """
    Flag only; blank in the report = unknown, never no (design D4).
    """

    yes = "yes"
    no = "no"
    unknown = "unknown"


class SnapshotTrust(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: Annotated[
        str, Field(json_schema_extra={"handling": "K"}, max_length=200, min_length=1)
    ]
    registration_ref: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=120, min_length=1),
    ] = None


class Designation(StrEnum):
    chairman = "chairman"
    secretary = "secretary"
    authorised_person = "authorised_person"


class SnapshotSignatory(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: Annotated[
        str,
        Field(
            json_schema_extra={"handling": "T", "token-field": "signatory_token"},
            max_length=200,
            min_length=1,
        ),
    ]
    """
    Chairman/Secretary name, used only for the M6 signer check (§2.8). Tokenised at the gateway (keyed HMAC-SHA256) before anything is stored; stored as signatory_token.
    """
    designation: Annotated[Designation, Field(json_schema_extra={"handling": "K"})]


class ApprovedIntake(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    ay: Annotated[AcademicYear, Field(json_schema_extra={"handling": "K"})]
    intake: Annotated[int, Field(ge=0, json_schema_extra={"handling": "K"})]


class SnapshotCourse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    programme: Annotated[
        str, Field(json_schema_extra={"handling": "K"}, max_length=200, min_length=1)
    ]
    level: Annotated[
        str, Field(json_schema_extra={"handling": "K"}, max_length=32, min_length=1)
    ]
    course: Annotated[
        str, Field(json_schema_extra={"handling": "K"}, max_length=200, min_length=1)
    ]
    intake_approved: Annotated[
        list[ApprovedIntake] | None,
        Field(json_schema_extra={"handling": "K"}, max_length=2),
    ] = None
    """
    Intake approved for the last 2 AYs.
    """
    intake_applied: Annotated[int, Field(ge=0, json_schema_extra={"handling": "K"})]
    faculty_required: Annotated[
        int | None, Field(ge=0, json_schema_extra={"handling": "K"})
    ] = None
    faculty_actual: Annotated[
        int | None, Field(ge=0, json_schema_extra={"handling": "K"})
    ] = None
    nri_status: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=64, min_length=1),
    ] = None
    international_students_status: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=64, min_length=1),
    ] = None
    nba_status: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=64, min_length=1),
    ] = None


class Unit(StrEnum):
    acre = "acre"
    hectare = "hectare"
    sq_m = "sq_m"


class LatitudeHemisphere(StrEnum):
    N = "N"
    S = "S"


class LatitudeDms(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    deg: Annotated[int, Field(ge=0, json_schema_extra={"handling": "K"}, le=180)]
    min: Annotated[int, Field(ge=0, json_schema_extra={"handling": "K"}, le=59)]
    sec: Annotated[int, Field(ge=0, json_schema_extra={"handling": "K"}, le=59)]
    hemisphere: Annotated[
        LatitudeHemisphere,
        Field(json_schema_extra={"handling": "K"}, title="LatitudeHemisphere"),
    ]


class LongitudeHemisphere(StrEnum):
    E = "E"
    W = "W"


class LongitudeDms(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    deg: Annotated[int, Field(ge=0, json_schema_extra={"handling": "K"}, le=180)]
    min: Annotated[int, Field(ge=0, json_schema_extra={"handling": "K"}, le=59)]
    sec: Annotated[int, Field(ge=0, json_schema_extra={"handling": "K"}, le=59)]
    hemisphere: Annotated[
        LongitudeHemisphere,
        Field(json_schema_extra={"handling": "K"}, title="LongitudeHemisphere"),
    ]


class CoordinatesDms(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    lat: Annotated[
        LatitudeDms, Field(json_schema_extra={"handling": "K"}, title="LatitudeDms")
    ]
    lon: Annotated[
        LongitudeDms, Field(json_schema_extra={"handling": "K"}, title="LongitudeDms")
    ]


class SnapshotBank(BaseModel):
    """
    Account number is X (rejected), never part of this model.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    bank_name: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=200, min_length=1),
    ] = None
    ifsc: Annotated[
        str | None,
        Field(
            json_schema_extra={"handling": "K"},
            max_length=11,
            min_length=1,
            pattern="^[A-Z]{4}0[A-Z0-9]{6}$",
        ),
    ] = None


class FinanceHead(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    head: Annotated[
        str, Field(json_schema_extra={"handling": "K"}, max_length=200, min_length=1)
    ]
    income_paise: Annotated[
        int | None, Field(ge=0, json_schema_extra={"handling": "K"})
    ] = None
    expenditure_paise: Annotated[
        int | None, Field(ge=0, json_schema_extra={"handling": "K"})
    ] = None


class SnapshotFinance(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    fy: Annotated[
        str | None,
        Field(
            json_schema_extra={"handling": "K"},
            max_length=16,
            min_length=1,
            pattern="^[0-9]{4}-[0-9]{2}$",
        ),
    ] = None
    income_total_paise: Annotated[
        int | None, Field(ge=0, json_schema_extra={"handling": "K"})
    ] = None
    expenditure_total_paise: Annotated[
        int | None, Field(ge=0, json_schema_extra={"handling": "K"})
    ] = None
    heads: Annotated[
        list[FinanceHead] | None, Field(json_schema_extra={"handling": "K"})
    ] = None


class DeclarationItems(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    a: Annotated[bool | None, Field(json_schema_extra={"handling": "K"})] = None
    b: Annotated[bool | None, Field(json_schema_extra={"handling": "K"})] = None
    c: Annotated[bool | None, Field(json_schema_extra={"handling": "K"})] = None
    d: Annotated[bool | None, Field(json_schema_extra={"handling": "K"})] = None
    e: Annotated[bool | None, Field(json_schema_extra={"handling": "K"})] = None
    f: Annotated[bool | None, Field(json_schema_extra={"handling": "K"})] = None


class CategoryListItem(RootModel[str]):
    root: Annotated[
        str, Field(json_schema_extra={"handling": "K"}, max_length=200, min_length=1)
    ]


class SnapshotDeclaration(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    items: Annotated[
        DeclarationItems | None,
        Field(json_schema_extra={"handling": "K"}, title="DeclarationItems"),
    ] = None
    category_list: Annotated[
        list[CategoryListItem] | None, Field(json_schema_extra={"handling": "K"})
    ] = None


class Deficiency(StrEnum):
    yes = "yes"
    no = "no"


class DeficiencySection(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    section: Annotated[
        str, Field(json_schema_extra={"handling": "R"}, max_length=200, min_length=1)
    ]
    deficiency: Annotated[Deficiency, Field(json_schema_extra={"handling": "R"})]


class Overall(StrEnum):
    yes = "yes"
    no = "no"
    unknown = "unknown"


class PrincipalEligibility(StrEnum):
    """
    The only HOI-derived value SATYA keeps (HOI personal details are X).
    """

    yes = "yes"
    no = "no"
    unknown = "unknown"


class DeficiencyReportResult(BaseModel):
    """
    Portal Deficiency Report result, imported not recomputed (D2, guard rail 8).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    template_year: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "R"}, max_length=16, min_length=1),
    ] = None
    sections: Annotated[
        list[DeficiencySection] | None, Field(json_schema_extra={"handling": "R"})
    ] = None
    overall: Annotated[Overall, Field(json_schema_extra={"handling": "R"})]
    principal_eligibility: Annotated[
        PrincipalEligibility | None, Field(json_schema_extra={"handling": "R"})
    ] = None
    """
    The only HOI-derived value SATYA keeps (HOI personal details are X).
    """


class BlockCount(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    expected: Annotated[int, Field(ge=0)]
    found: Annotated[int, Field(ge=0)]


class CaseId(RootModel[str]):
    root: Annotated[str, Field(pattern="^cas_[0-9A-HJKMNP-TV-Z]{26}$", title="CaseId")]


class LabelCounts(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    verified: Annotated[int, Field(ge=0)]
    mismatch_detected: Annotated[int, Field(ge=0)]
    expired: Annotated[int, Field(ge=0)]
    verification_pending: Annotated[int, Field(ge=0)]
    source_unavailable: Annotated[int, Field(ge=0)]
    manual_review_required: Annotated[int, Field(ge=0)]


class FormatType(StrEnum):
    """
    T = AICTE template, E = external, P = portal data (design B).
    """

    T = "T"
    E = "E"
    P = "P"


class AdapterMode(StrEnum):
    """
    Same values as CheckSource.mode; every mock result is shown as MOCK SOURCE.
    """

    live = "live"
    mock = "mock"
    offline = "offline"
    none = "none"


class VerificationSource(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    channel: Annotated[str, Field(max_length=120, min_length=1)]
    """
    e.g. 'pdf-signature' (offline chain check), 'icai-udin', 'tn-fire-licence'.
    """
    adapter_mode: AdapterMode
    """
    Same values as CheckSource.mode; every mock result is shown as MOCK SOURCE.
    """


class VerificationAction(StrEnum):
    recheck = "recheck"
    route_manual = "route_manual"
    retry = "retry"


class CategoryName(RootModel[str]):
    root: Annotated[str, Field(max_length=200, min_length=1, title="CategoryName")]
    """
    An application category as printed in the affidavit's numbered category line, e.g. EoA Only.
    """


class CheckKind(StrEnum):
    issuer_signature = "issuer_signature"
    uploader_signature = "uploader_signature"
    source_lookup = "source_lookup"
    qr_consistency = "qr_consistency"
    expiry = "expiry"
    format = "format"
    chronology = "chronology"


class FieldDiff(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    field: Annotated[str, Field(min_length=1)]
    submitted: str | float | bool | None
    source: str | float | bool | None


class ExpiryBasis(StrEnum):
    printed = "printed"
    computed_from_state_rule = "computed_from_state_rule"


class SourceMode(StrEnum):
    live = "live"
    mock = "mock"
    offline = "offline"
    none = "none"


class CheckSource(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    adapter_id: Annotated[str, Field(pattern="^[a-z0-9][a-z0-9-]{1,63}$")]
    mode: Annotated[SourceMode, Field(title="SourceMode")]
    name: Annotated[str, Field(max_length=200, min_length=1)]


class CorrelationId(RootModel[str]):
    root: Annotated[
        str, Field(pattern="^cor_[0-9A-HJKMNP-TV-Z]{26}$", title="CorrelationId")
    ]


class Date(RootModel[date]):
    root: Annotated[date, Field(title="Date")]


class DeclarationBlock(StrEnum):
    """
    core = 19 core declarations; existing_institute = 5 'Existing Institute' declarations; extra = a block the 2024-27 draft does not print (e.g. a 2023-24-style Increase-in-Intake block).
    """

    core = "core"
    existing_institute = "existing_institute"
    extra = "extra"


class DispositionAction(StrEnum):
    accept = "accept"
    override = "override"
    escalate_clarify = "escalate_clarify"
    escalate_refer = "escalate_refer"
    escalate_manual = "escalate_manual"


class DocId(RootModel[str]):
    root: Annotated[str, Field(pattern="^doc_[0-9A-HJKMNP-TV-Z]{26}$", title="DocId")]


class EventId(RootModel[str]):
    root: Annotated[str, Field(pattern="^evt_[0-9A-HJKMNP-TV-Z]{26}$", title="EventId")]


class EventType(StrEnum):
    """
    All inbound and outbound event types.
    """

    application_precheck_requested = "application.precheck_requested"
    application_submitted = "application.submitted"
    application_reopened = "application.reopened"
    committee_scrutiny_constituted = "committee.scrutiny_constituted"
    committee_rescrutiny_constituted = "committee.rescrutiny_constituted"
    deficiency_posted = "deficiency.posted"
    evc_selection_round_opened = "evc.selection_round_opened"
    evc_selection_recorded = "evc.selection_recorded"
    evc_scheduled = "evc.scheduled"
    evc_media_submitted = "evc.media_submitted"
    hearing_scheduled = "hearing.scheduled"
    compliance_submitted = "compliance.submitted"
    decision_recorded = "decision.recorded"
    eoa_letter_issued = "eoa.letter_issued"
    enrolment_uploaded = "enrolment.uploaded"
    faculty_record_changed = "faculty.record_changed"
    complaint_referred = "complaint.referred"
    precheck_completed = "precheck.completed"
    case_validation_completed = "case.validation_completed"
    case_evidence_pack_ready = "case.evidence_pack_ready"
    evc_selection_proposal_ready = "evc.selection_proposal_ready"
    evc_checklist_ready = "evc.checklist_ready"
    evc_media_check_completed = "evc.media_check_completed"
    case_dossier_ready = "case.dossier_ready"
    document_status_changed = "document.status_changed"
    alert_raised = "alert.raised"
    observation_recorded = "observation.recorded"
    observation_withdrawn = "observation.withdrawn"
    clarification_requested = "clarification.requested"
    referral_recommended = "referral.recommended"
    deficiency_candidates_proposed = "deficiency.candidates_proposed"
    ingest_failed = "ingest.failed"


class ExtractedSource(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    doc_label: Annotated[str, Field(max_length=200, min_length=1)]
    page: Annotated[int | None, Field(ge=1)]
    row: str | int | None = None


class ExpectedSource(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    label: Annotated[str, Field(max_length=200, min_length=1)]


class ConfidenceBand(StrEnum):
    high = "high"
    medium = "medium"
    low = "low"


class Provenance(StrEnum):
    satya = "satya"
    portal = "portal"


class Stage(StrEnum):
    """
    C2 stage ①–⑦.
    """

    field_1 = "1"
    field_2 = "2"
    field_3 = "3"
    field_4 = "4"
    field_5 = "5"
    field_6 = "6"
    field_7 = "7"


class FlagId(RootModel[str]):
    root: Annotated[str, Field(pattern="^flg_[0-9A-HJKMNP-TV-Z]{26}$", title="FlagId")]


class InboundEventType(StrEnum):
    """
    Portal → SATYA (Portal spec §2.4).
    """

    application_precheck_requested = "application.precheck_requested"
    application_submitted = "application.submitted"
    application_reopened = "application.reopened"
    committee_scrutiny_constituted = "committee.scrutiny_constituted"
    committee_rescrutiny_constituted = "committee.rescrutiny_constituted"
    deficiency_posted = "deficiency.posted"
    evc_selection_round_opened = "evc.selection_round_opened"
    evc_selection_recorded = "evc.selection_recorded"
    evc_scheduled = "evc.scheduled"
    evc_media_submitted = "evc.media_submitted"
    hearing_scheduled = "hearing.scheduled"
    compliance_submitted = "compliance.submitted"
    decision_recorded = "decision.recorded"
    eoa_letter_issued = "eoa.letter_issued"
    enrolment_uploaded = "enrolment.uploaded"
    faculty_record_changed = "faculty.record_changed"
    complaint_referred = "complaint.referred"


class OutboundEventType(StrEnum):
    """
    SATYA → portal (Portal spec §2.5), all advisory.
    """

    precheck_completed = "precheck.completed"
    case_validation_completed = "case.validation_completed"
    case_evidence_pack_ready = "case.evidence_pack_ready"
    evc_selection_proposal_ready = "evc.selection_proposal_ready"
    evc_checklist_ready = "evc.checklist_ready"
    evc_media_check_completed = "evc.media_check_completed"
    case_dossier_ready = "case.dossier_ready"
    document_status_changed = "document.status_changed"
    alert_raised = "alert.raised"
    observation_recorded = "observation.recorded"
    observation_withdrawn = "observation.withdrawn"
    clarification_requested = "clarification.requested"
    referral_recommended = "referral.recommended"
    deficiency_candidates_proposed = "deficiency.candidates_proposed"
    ingest_failed = "ingest.failed"


class PermanentId(RootModel[str]):
    root: Annotated[str, Field(pattern="^1-[0-9]{7,11}$", title="PermanentId")]
    """
    Portal permanent ID in printed form (design D4).
    """


class PrintedItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: Annotated[
        str, Field(json_schema_extra={"handling": "R"}, max_length=200, min_length=1)
    ]
    value: Annotated[
        str, Field(json_schema_extra={"handling": "R"}, max_length=400, min_length=1)
    ]


class PrintedSection(BaseModel):
    """
    Portal-computed section kept as printed, display only (D2).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    items: Annotated[
        list[PrintedItem] | None, Field(json_schema_extra={"handling": "R"})
    ] = None


class ReadStatus(StrEnum):
    native = "native"
    ocr_read = "ocr_read"
    blocked = "blocked"


class ReadNote(BaseModel):
    """
    How a file was read: the PDF text layer, OCR of a scan, or not at all. The wording of the sentence is a translated template picked by `variant`. Text read by OCR never decides anything.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    status: Annotated[ReadStatus, Field(title="ReadStatus")]
    reason_code: Annotated[str | None, Field(max_length=40)]
    """
    Short code for auditors, for example SCAN_IMAGE_ONLY. The code is shared by a scan that was read and a scan that was not.
    """
    variant: Annotated[str | None, Field(max_length=40)]
    """
    Key of the plain sentence, for example scan_read, low_confidence, scan_not_attempted.
    """
    values: dict[str, str | float]
    """
    Numbers the sentence mentions (confidence, threshold, pages).
    """
    ocr_mean_confidence: Annotated[float | None, Field(ge=0.0, le=1.0)]


class ReceiptId(RootModel[str]):
    root: Annotated[
        str, Field(pattern="^rcp_[0-9A-HJKMNP-TV-Z]{26}$", title="ReceiptId")
    ]


class Region(BaseModel):
    """
    Evidence region on a page, normalised 0–1.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    x: Annotated[float, Field(ge=0.0, le=1.0)]
    y: Annotated[float, Field(ge=0.0, le=1.0)]
    w: Annotated[float, Field(ge=0.0, le=1.0)]
    h: Annotated[float, Field(ge=0.0, le=1.0)]


class RiskBand(StrEnum):
    """
    Risk band (decision #20). Orders review only; never a 0–100 score; never shown to the institution.
    """

    high = "high"
    medium = "medium"
    low = "low"


class Role(StrEnum):
    """
    Keycloak realm roles (UI spec §1).
    """

    RB = "RB"
    SC = "SC"
    EV = "EV"
    HC = "HC"
    RA = "RA"
    AU = "AU"
    INS = "INS"


class RoomRow(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    room_id: Annotated[
        str, Field(json_schema_extra={"handling": "K"}, max_length=64, min_length=1)
    ]
    room_type: Annotated[
        str, Field(json_schema_extra={"handling": "K"}, max_length=120, min_length=1)
    ]
    carpet_area_m2: Annotated[float, Field(ge=0.0, json_schema_extra={"handling": "K"})]
    flooring: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=32, min_length=1),
    ] = None
    """
    Completion of flooring, as printed (e.g. Ready).
    """
    walls_painting: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=32, min_length=1),
    ] = None
    electrification: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=32, min_length=1),
    ] = None


class RunId(RootModel[str]):
    root: Annotated[str, Field(pattern="^run_[0-9A-HJKMNP-TV-Z]{26}$", title="RunId")]


class Severity(StrEnum):
    info = "info"
    warning = "warning"
    critical = "critical"


class Sha256(RootModel[str]):
    root: Annotated[str, Field(pattern="^[0-9a-f]{64}$", title="Sha256")]


class SignatureRole(StrEnum):
    issuer = "issuer"
    uploader = "uploader"


class SignatureState(StrEnum):
    verified = "verified"
    image_only = "image_only"
    chain_broken = "chain_broken"
    edited_after_signing = "edited_after_signing"
    not_digital = "not_digital"
    not_applicable = "not_applicable"
    present = "present"
    absent_required = "absent_required"


class SignerRole(StrEnum):
    chairman = "chairman"
    secretary = "secretary"
    issuer = "issuer"
    unknown = "unknown"


class SignatureCheck(BaseModel):
    """
    One of the two independent signature checks (Portal spec §2.8, UI spec §4.3). An image-only mark is never verified (decision #16).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    role: Annotated[SignatureRole, Field(title="SignatureRole")]
    state: Annotated[SignatureState, Field(title="SignatureState")]
    has_byte_range: bool
    """
    true only for a real CMS signature (/ByteRange).
    """
    reason_code: Annotated[str | None, Field(pattern="^[A-Z][A-Z0-9_]{1,63}$")] = None
    page: Annotated[int | None, Field(ge=1)] = None
    signer_role: SignerRole | None = None
    trust_anchor_label: Annotated[str | None, Field(max_length=64)] = None
    """
    Demo chain anchors are always 'TEST TRUST ANCHOR' (guard rail 10).
    """


class Subject(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    application_id: ApplicationId
    permanent_id: PermanentId | None = None
    ay: AcademicYear


class Timestamp(RootModel[AwareDatetime]):
    root: Annotated[AwareDatetime, Field(title="Timestamp")]
    """
    RFC 3339 date-time with offset (format-checked; Pydantic AwareDatetime); stored UTC, shown IST.
    """


class VerificationLabel(StrEnum):
    """
    The six PS verification labels (Portal spec §2.6.3). Document label = most severe check outcome, in x-precedence order (most severe first). `verified` also requires at least one authenticity check; a valid uploader DSC never makes a document verified.
    """

    verified = "verified"
    mismatch_detected = "mismatch_detected"
    expired = "expired"
    verification_pending = "verification_pending"
    source_unavailable = "source_unavailable"
    manual_review_required = "manual_review_required"


class DecidedBy(StrEnum):
    system = "system"
    official = "official"


class YoyVerdict(StrEnum):
    """
    M13 year-over-year verdict (design C4a): explained by an approved application, or a discrepancy.
    """

    explained = "explained"
    discrepancy = "discrepancy"


class AffidavitCase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    case_id: CaseId
    application_id: ApplicationId
    permanent_id: PermanentId | None = None
    ay: AcademicYear
    regional_office: Annotated[str, Field(max_length=64, min_length=1)]
    institution_name: Annotated[str | None, Field(max_length=200, min_length=1)] = None
    route: Annotated[CaseRoute, Field(title="CaseRoute")]
    """
    Table 2.3 route (UI spec §6).
    """
    stage: Annotated[CaseStage, Field(title="CaseStage")]
    """
    C2 stage ①–⑦.
    """
    category_set: list[CategoryName]


class ExpectedDeclaration(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    no: Annotated[int, Field(ge=1)]
    """
    Canonical position 1–24 (core 1–19, existing institute 20–24).
    """
    printed_no: Annotated[int, Field(ge=1)]
    """
    Number as printed in the draft; numbering restarts in the existing-institute block (design B1 row 1).
    """
    block: DeclarationBlock
    text: Annotated[str, Field(max_length=4000, min_length=1)]


class AffidavitExpected(BaseModel):
    """
    Portal-generated Affidavit 2 for this AID and AY.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    template_id: Annotated[str, Field(max_length=120, min_length=1)]
    template_year: Annotated[str, Field(max_length=16, min_length=1)]
    """
    APH edition the template belongs to, e.g. 2024-27.
    """
    aid: ApplicationId
    category_list: list[CategoryName]
    declarations: list[ExpectedDeclaration]


class SwornDeclaration(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    no: Annotated[int, Field(ge=1)]
    """
    Position in the sworn copy, counted across blocks.
    """
    printed_no: Annotated[int | None, Field(ge=1)]
    """
    Number as printed in the sworn copy.
    """
    block: DeclarationBlock
    text: Annotated[str, Field(max_length=4000, min_length=1)]
    page: Annotated[int, Field(ge=1)]
    region: Region
    ocr_confidence: Annotated[float | None, Field(ge=0.0, le=1.0)]


class AffidavitSworn(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    page_count: Annotated[int, Field(ge=0)]
    sha256: Sha256
    template_match: bool
    """
    The sworn copy's heading and AY line identify the expected template.
    """
    template_detected: Annotated[str | None, Field(max_length=120)] = None
    text_source: Annotated[TextSource, Field(title="TextSource")]
    """
    Where the sworn text came from: the PDF text layer, or OCR of a scanned file. Text read by OCR never decides anything.
    """
    ocr_mean_confidence: Annotated[float | None, Field(ge=0.0, le=1.0)]
    """
    null for a text layer.
    """
    issuer_sig: SignatureCheck | None
    """
    Filled by the signature check; null when it could not read the file.
    """
    uploader_sig: SignatureCheck | None
    """
    Filled by the signature check; null when it could not read the file.
    """
    category_list_found: list[CategoryName] | None
    """
    null when no category line was found.
    """
    declarations: list[SwornDeclaration]


class DiffOp(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    op: Annotated[DiffOpKind, Field(title="DiffOpKind")]
    decl_no: Annotated[int | None, Field(ge=1)]
    """
    Canonical expected position 1–24; null for an added declaration.
    """
    sworn_no: Annotated[int | None, Field(ge=1)]
    """
    Position of the matched declaration in the sworn copy (see sworn.declarations[].no); null for a removed declaration.
    """
    similarity: Annotated[float, Field(ge=0.0, le=1.0)]
    flag_id: FlagId | None = None
    spans: list[DiffSpan]


class CategoryLineCheck(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    expected: list[CategoryName]
    found: list[CategoryName]
    state: Annotated[CategoryLineState, Field(title="CategoryLineState")]
    page: Annotated[int | None, Field(ge=1)] = None
    flag_id: FlagId | None = None


class AffidavitStructure(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    category_line: Annotated[CategoryLineCheck, Field(title="CategoryLineCheck")]
    core: BlockCount
    existing_institute: BlockCount
    extra_blocks: list[ExtraBlock]


class AffidavitTableRow(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    key: Annotated[str, Field(max_length=120, min_length=1)]
    """
    Row key: deed row number (land) or room ID (rooms).
    """
    state: Annotated[TableRowState, Field(title="TableRowState")]
    page: Annotated[int | None, Field(ge=1)] = None
    region: Region | None = None
    sworn_cells: list[SwornCell | None]
    application_report_cells: list[ApplicationReportCell | None]
    cell_match: list[bool | None]
    delta: float | None = None
    flag_ids: list[FlagId] | None = None


class AffidavitTable(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    table: Annotated[AffidavitTableName, Field(title="AffidavitTableName")]
    columns: list[Column]
    """
    Field keys in column order, e.g. area_acre; the UI translates them.
    """
    rows: list[AffidavitTableRow]
    total_rows: Annotated[int, Field(ge=0)]
    computed_total_acres: Annotated[float | None, Field(ge=0.0)]
    """
    Land only: sum of sworn deed areas (the portal leaves the total blank).
    """
    expected_total_acres: Annotated[float | None, Field(ge=0.0)]
    """
    Land only: ApplicationSnapshot land.total_area in acres.
    """
    room_id_duplicates: list[RoomIdDuplicate]
    """
    Room IDs used more than once across the 4 room tables.
    """


class AffidavitStamp(BaseModel):
    """
    Filled by the signature and stamp check from the stamp page; null when no stamp page is found.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    instrument: Annotated[str, Field(max_length=64, min_length=1)]
    certificate_no: Annotated[str | None, Field(max_length=64)]
    second_party: Annotated[str | None, Field(max_length=200)]
    duty: Annotated[int | None, Field(ge=0)]
    """
    Stamp duty in paise (Portal §2 conventions).
    """
    state: VerificationLabel
    article: Annotated[str | None, Field(max_length=120)] = None
    """
    Description of document on the stamp, e.g. 'Article 4 Affidavit'.
    """
    issue_date: Date | None = None
    page: Annotated[int | None, Field(ge=1)] = None


class AffidavitChronology(BaseModel):
    """
    Application ≤ stamp ≤ notarisation ≤ DSC ≤ upload (design B1 row 1, D1). Filled by the signature and stamp check.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    application_date: Date | None
    stamp_date: Date | None
    notary_date: Date | None
    dsc_date: Date | None = None
    upload_date: Date | None
    order_ok: bool | None
    notary_expiry: Date | None = None
    dsc_kind: DscKind | None = None
    """
    Where dsc_date comes from: a real CMS signature or a printed mark (image only).
    """
    mark_after_notary: bool | None = None
    """
    A printed signature mark dated after the notarisation (design D1 review case); null when there is no mark.
    """
    notary_expiry_ok: bool | None = None


class Comparison(BaseModel):
    """
    Whether the sworn copy was really compared with the portal draft. Added by the API; the page says a copy matches only when state is compared. A scan or an unreadable file is not_compared: OCR text never decides anything.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    state: Annotated[ComparisonState, Field(title="ComparisonState")]
    source: Annotated[ComparisonSource, Field(title="ComparisonSource")]
    """
    Where the sworn text came from, or why there is none.
    """
    read: ReadNote


class Alert(BaseModel):
    """
    Alert with type + subtype (Portal spec §2.9). Institution-facing alerts are limited to missing_info, expired, unresolved.clarification_* and unresolved.compliance_window_*.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    alert_id: AlertId
    type: AlertType
    subtype: AlertSubtype
    severity: Severity
    audience_roles: Annotated[list[Role], Field(min_length=1)]
    case_id: CaseId
    application_id: ApplicationId
    flag_id: FlagId | None = None
    doc_id: DocId | None = None
    label: VerificationLabel | None = None
    aph_clause: Annotated[str | None, Field(max_length=64, min_length=1)] = None
    text_key: Annotated[str, Field(max_length=128, min_length=1)]
    due_at: Timestamp | None = None
    created_at: Timestamp
    read: bool


class SnapshotBasic(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    application_id: Annotated[ApplicationId, Field(json_schema_extra={"handling": "K"})]
    permanent_id: Annotated[
        PermanentId | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    institution_type: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=120, min_length=1),
    ] = None
    status: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=120, min_length=1),
    ] = None
    application_date: Annotated[
        Date | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    submission_date: Annotated[
        Date | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    regional_office: Annotated[
        str, Field(json_schema_extra={"handling": "K"}, max_length=64, min_length=1)
    ]
    overall_deficiency: Annotated[
        TriState, Field(json_schema_extra={"handling": "K"}, title="TriState")
    ]
    """
    Flag only; blank in the report = unknown, never no (design D4).
    """


class SnapshotTrustee(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: Annotated[
        str,
        Field(
            json_schema_extra={"handling": "T", "token-field": "trustee_token"},
            max_length=200,
            min_length=1,
        ),
    ]
    """
    Trustee name. Tokenised at the gateway (keyed HMAC-SHA256) before anything is stored; stored as trustee_token.
    """
    role: Annotated[
        str, Field(json_schema_extra={"handling": "K"}, max_length=64, min_length=1)
    ]
    tenure_from: Annotated[Date | None, Field(json_schema_extra={"handling": "K"})] = (
        None
    )
    tenure_to: Annotated[Date | None, Field(json_schema_extra={"handling": "K"})] = None


class SnapshotDeed(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    holder: Annotated[
        str,
        Field(
            json_schema_extra={"handling": "T", "token-field": "holder_token"},
            max_length=200,
            min_length=1,
        ),
    ]
    """
    Deed holder. Tokenised at the gateway (keyed HMAC-SHA256) before anything is stored; stored as holder_token.
    """
    document_no: Annotated[
        str,
        Field(
            json_schema_extra={"handling": "T", "token-field": "deed_token"},
            max_length=200,
            min_length=1,
        ),
    ]
    """
    Deed document number. Tokenised at the gateway (keyed HMAC-SHA256) before anything is stored; stored as deed_token.
    """
    registration_date: Annotated[
        Date | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    plot_no: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=64, min_length=1),
    ] = None
    village_district: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=200, min_length=1),
    ] = None
    area_acre: Annotated[float, Field(ge=0.0, json_schema_extra={"handling": "K"})]


class SnapshotLand(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    total_area: Annotated[
        float | None, Field(ge=0.0, json_schema_extra={"handling": "K"})
    ] = None
    unit: Annotated[Unit | None, Field(json_schema_extra={"handling": "K"})] = None
    pieces: Annotated[int | None, Field(ge=0, json_schema_extra={"handling": "K"})] = (
        None
    )
    max_distance_km: Annotated[
        float | None, Field(ge=0.0, json_schema_extra={"handling": "K"})
    ] = None
    land_use_certificate_issuer: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=200, min_length=1),
    ] = None
    land_use_certificate_date: Annotated[
        Date | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    coordinates: Annotated[
        CoordinatesDms | None,
        Field(json_schema_extra={"handling": "K"}, title="CoordinatesDms"),
    ] = None
    deeds: Annotated[
        list[SnapshotDeed] | None, Field(json_schema_extra={"handling": "K"})
    ] = None


class SnapshotBuilding(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    block: Annotated[
        str, Field(json_schema_extra={"handling": "K"}, max_length=200, min_length=1)
    ]
    sanctioned_area_m2: Annotated[
        float | None, Field(ge=0.0, json_schema_extra={"handling": "K"})
    ] = None
    constructed_area_m2: Annotated[
        float | None, Field(ge=0.0, json_schema_extra={"handling": "K"})
    ] = None
    approving_authority: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=200, min_length=1),
    ] = None
    approval_date: Annotated[
        Date | None, Field(json_schema_extra={"handling": "K"})
    ] = None


class SnapshotRooms(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    administrative: Annotated[
        list[RoomRow] | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    amenities: Annotated[
        list[RoomRow] | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    instructional: Annotated[
        list[RoomRow] | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    instructional_common: Annotated[
        list[RoomRow] | None, Field(json_schema_extra={"handling": "K"})
    ] = None


class SnapshotFaculty(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    faculty_id: Annotated[
        str,
        Field(
            json_schema_extra={"handling": "T", "token-field": "faculty_token"},
            max_length=200,
            min_length=1,
        ),
    ]
    """
    Portal Faculty ID (1- + 9–11 digits). Reveal only via a logged official action (AU-04). Tokenised at the gateway (keyed HMAC-SHA256) before anything is stored; stored as faculty_token.
    """
    designation: Annotated[
        str, Field(json_schema_extra={"handling": "K"}, max_length=64, min_length=1)
    ]
    appointment_type: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=64, min_length=1),
    ] = None
    programme: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=200, min_length=1),
    ] = None
    department: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=200, min_length=1),
    ] = None
    date_of_joining: Annotated[
        Date | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    highest_qualification_level: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "K"}, max_length=64, min_length=1),
    ] = None
    relieved_date: Annotated[
        Date | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    is_duplicate: Annotated[bool | None, Field(json_schema_extra={"handling": "R"})] = (
        None
    )
    """
    Portal's own within-portal duplicate flag (D2); never recomputed.
    """
    pan_validation: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "R"}, max_length=32, min_length=1),
    ] = None
    """
    Portal's PAN validation result only (D2); the PAN itself is X.
    """
    record_status: Annotated[
        str | None,
        Field(json_schema_extra={"handling": "R"}, max_length=32, min_length=1),
    ] = None


class ApplicationSnapshot(BaseModel):
    """
    The Application Report field set as the portal sends it (Portal spec §2.6.1). Every property carries x-handling: K keep, T tokenise (keyed HMAC-SHA256, key never stored with the data), R result only (portal's computed value, D2). Fields marked X must not be sent and do not exist in this model; they are listed in x-rejected-fields and the gateway answers PERSONAL_DATA_REJECTED. Unknown fields are rejected (additionalProperties false) for data minimisation.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    ay: Annotated[AcademicYear, Field(json_schema_extra={"handling": "K"})]
    captured_at: Annotated[
        Timestamp | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    basic: Annotated[
        SnapshotBasic, Field(json_schema_extra={"handling": "K"}, title="SnapshotBasic")
    ]
    trust: Annotated[
        SnapshotTrust | None,
        Field(json_schema_extra={"handling": "K"}, title="SnapshotTrust"),
    ] = None
    trustees: Annotated[
        list[SnapshotTrustee] | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    authorised_signatory: Annotated[
        SnapshotSignatory | None,
        Field(json_schema_extra={"handling": "K"}, title="SnapshotSignatory"),
    ] = None
    courses: Annotated[
        list[SnapshotCourse] | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    land: Annotated[
        SnapshotLand | None,
        Field(json_schema_extra={"handling": "K"}, title="SnapshotLand"),
    ] = None
    buildings: Annotated[
        list[SnapshotBuilding] | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    rooms: Annotated[
        SnapshotRooms | None,
        Field(json_schema_extra={"handling": "K"}, title="SnapshotRooms"),
    ] = None
    facilities: Annotated[
        PrintedSection | None, Field(json_schema_extra={"handling": "R"})
    ] = None
    committees: Annotated[
        PrintedSection | None, Field(json_schema_extra={"handling": "R"})
    ] = None
    bank: Annotated[
        SnapshotBank | None,
        Field(json_schema_extra={"handling": "K"}, title="SnapshotBank"),
    ] = None
    """
    Account number is X (rejected), never part of this model.
    """
    finance: Annotated[
        SnapshotFinance | None,
        Field(json_schema_extra={"handling": "K"}, title="SnapshotFinance"),
    ] = None
    declaration: Annotated[
        SnapshotDeclaration | None,
        Field(json_schema_extra={"handling": "K"}, title="SnapshotDeclaration"),
    ] = None
    faculty: Annotated[
        list[SnapshotFaculty] | None, Field(json_schema_extra={"handling": "K"})
    ] = None
    deficiency_report: Annotated[
        DeficiencyReportResult | None,
        Field(json_schema_extra={"handling": "R"}, title="DeficiencyReportResult"),
    ] = None
    """
    Portal Deficiency Report result, imported not recomputed (D2, guard rail 8).
    """


class CheckEvidence(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    page: Annotated[int, Field(ge=1)]
    regions: list[Region] | None = None


class Check(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    kind: Annotated[CheckKind, Field(title="CheckKind")]
    outcome: VerificationLabel
    reason_code: Annotated[str, Field(pattern="^[A-Z][A-Z0-9_]{1,63}$")]
    evidence: Annotated[CheckEvidence | None, Field(title="CheckEvidence")] = None
    source: CheckSource | None = None
    checked_at: Timestamp | None = None
    response_sha256: Sha256 | None = None
    attempts: Annotated[int | None, Field(ge=0)] = None
    field_diff: list[FieldDiff] | None = None
    """
    Drives mismatch_detected.
    """
    valid_from: Date | None = None
    valid_to: Date | None = None
    basis: Annotated[ExpiryBasis | None, Field(title="ExpiryBasis")] = None
    check_ref: Annotated[str | None, Field(max_length=128)] = None
    """
    Links the check to the flag it raised (Flag.check_ref), e.g. m6:STAMP-CHRONO:chronology:order.
    """
    signed_at: Timestamp | None = None
    """
    Signature checks: signing time claimed in the CMS signature (the validation moment).
    """
    trust_anchor_label: Annotated[str | None, Field(max_length=64)] = None
    """
    Signature checks: the anchor the chain built to; demo chains are always 'TEST TRUST ANCHOR' (guard rail 10).
    """


class Disposition(BaseModel):
    """
    An official's recorded decision on a flag (Portal spec §2.6.5; UI spec §4.2). No action changes regulatory status; undo is a new ledger entry.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    action: Annotated[DispositionAction, Field(title="DispositionAction")]
    reason: Annotated[str, Field(max_length=4000, min_length=10)]
    reason_template_id: Annotated[str | None, Field(max_length=64)] = None
    by_user_ref: Annotated[str, Field(max_length=128, min_length=1)]
    """
    Opaque user reference (Keycloak subject), never a name.
    """
    by_role: Role
    at: Timestamp
    ledger_no: Annotated[int, Field(ge=1)]


class EventEnvelope(BaseModel):
    """
    Event envelope for both directions (Portal spec §2.3). Every inbound type is a proposed hook that the mock portal implements (guard rail 2). Outbound events must carry advisory: true and regulatory_effect: none (guard rail 1). Consumers ignore unknown top-level fields (§2.12).
    """

    spec: Literal["satya.event/1"]
    event_id: EventId
    type: EventType
    occurred_at: Timestamp
    producer: Annotated[str, Field(pattern="^[a-z][a-z0-9-]{1,40}$")]
    """
    e.g. mock-portal, satya
    """
    subject: Subject
    sequence: Annotated[int, Field(ge=1)]
    """
    Per application, increases by 1.
    """
    correlation_id: CorrelationId
    data: dict[str, Any]
    """
    Type-specific payload (§2.4, §2.5). Per-type payload.
    """
    advisory: Literal[True] | None = None
    regulatory_effect: Literal["none"] | None = None
    case_id: CaseId | None = None
    run_id: RunId | None = None
    deep_link: Annotated[str | None, Field(pattern="^/[A-Za-z0-9/_-]{1,200}$")] = None
    """
    Opaque path; no personal data, no tokens.
    """


class FlagYoy(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    ay_a_ref: Annotated[str, Field(max_length=128, min_length=1)]
    ay_b_ref: Annotated[str, Field(max_length=128, min_length=1)]
    verdict: YoyVerdict


class Flag(BaseModel):
    """
    An evidence-linked finding (Portal spec §2.6.4). Every flag cites rule_id + rule_version + aph_clause + aph_edition (guard rail 6). Anomaly/forgery-type flags carry preliminary_indicator: true (PS FR2).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    flag_id: FlagId
    doc_id: DocId | None
    """
    null for snapshot-level findings.
    """
    page: Annotated[int | None, Field(ge=1)]
    regions: list[Region]
    rule_id: Annotated[str, Field(pattern="^[A-Z][A-Z0-9-]{1,63}$")]
    rule_version: Annotated[str, Field(max_length=32, min_length=1)]
    rule_text_key: Annotated[str, Field(max_length=128, min_length=1)]
    aph_clause: Annotated[str, Field(max_length=64, min_length=1)]
    aph_edition: Annotated[str, Field(max_length=32, min_length=1)]
    """
    e.g. 2024-27
    """
    extracted_value: str | float | bool | None
    expected_value: str | float | bool | None
    value_unit: Annotated[str | None, Field(max_length=32)]
    delta: float | None = None
    extracted_source: Annotated[ExtractedSource, Field(title="ExtractedSource")]
    expected_source: Annotated[ExpectedSource, Field(title="ExpectedSource")]
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    confidence_band: Annotated[ConfidenceBand, Field(title="ConfidenceBand")]
    label: VerificationLabel
    provenance: Annotated[Provenance, Field(title="Provenance")]
    preliminary_indicator: bool
    severity: Severity
    disposition: Disposition | None
    check_ref: Annotated[str | None, Field(max_length=128)] = None
    stage: Annotated[Stage, Field(title="Stage")]
    """
    C2 stage ①–⑦.
    """
    institution_visible: bool
    yoy: Annotated[FlagYoy | None, Field(title="FlagYoy")] = None
    evidence_sha256: Sha256


class VerificationResult(BaseModel):
    """
    Per-document verification with all checks (Portal spec §2.7). Every mock result is shown as MOCK SOURCE (guard rail 10).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    doc_id: DocId
    label: VerificationLabel
    decided_by: Annotated[DecidedBy, Field(title="DecidedBy")]
    basis_note: Annotated[str | None, Field(max_length=4000, min_length=10)] = None
    """
    Required when an official resolves the label.
    """
    checks: list[Check]


class AffidavitDiff(BaseModel):
    """
    RB-05 DiffView payload, GET /v1/cases/{case_id}/affidavit-diff (UI spec §6.3, §7.1; design B1 row 1, C3). M5 output: the sworn Affidavit 2 compared clause by clause with the portal draft for the same AID and AY, and its land and room tables reconciled with the ApplicationSnapshot. Advisory only. Identifier cells that the gateway tokenises (deed holder, deed document no.) are masked.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    case: Annotated[AffidavitCase, Field(title="AffidavitCase")]
    doc_id: DocId
    run_id: RunId | None = None
    engine_version: Annotated[str, Field(max_length=32, min_length=1)]
    ruleset_version: Annotated[str, Field(max_length=64, min_length=1)]
    advisory: Literal[True]
    expected: Annotated[AffidavitExpected, Field(title="AffidavitExpected")]
    """
    Portal-generated Affidavit 2 for this AID and AY.
    """
    sworn: Annotated[AffidavitSworn, Field(title="AffidavitSworn")]
    normalisation: Annotated[
        AffidavitNormalisation, Field(title="AffidavitNormalisation")
    ]
    options: list[DeclarationOption]
    ops: list[DiffOp]
    structure: Annotated[AffidavitStructure, Field(title="AffidavitStructure")]
    tables: list[AffidavitTable]
    stamp: AffidavitStamp | None
    """
    Filled by the signature and stamp check from the stamp page; null when no stamp page is found.
    """
    chronology: AffidavitChronology | None
    """
    Application ≤ stamp ≤ notarisation ≤ DSC ≤ upload (design B1 row 1, D1). Filled by the signature and stamp check.
    """
    comparison: Annotated[Comparison | None, Field(title="Comparison")] = None
    """
    Whether the sworn copy was really compared with the portal draft. Added by the API; the page says a copy matches only when state is compared. A scan or an unreadable file is not_compared: OCR text never decides anything.
    """
    pending: list[PendingSection]
    """
    DiffView sections whose checks belong to a later module, so the UI can say so instead of showing an empty panel.
    """
    flags: list[Flag]


class CaseVerificationDocument(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    doc_id: DocId
    slot: Annotated[str, Field(max_length=120, min_length=1)]
    title: Annotated[str, Field(max_length=200, min_length=1)]
    format_type: FormatType
    """
    T = AICTE template, E = external, P = portal data (design B).
    """
    state_code: Annotated[str | None, Field(pattern="^[A-Z]{2}$")]
    issuer_profile: Annotated[str | None, Field(max_length=120)]
    """
    Annexure-14 issuer profile id; null when none is recorded.
    """
    source: Annotated[VerificationSource, Field(title="VerificationSource")]
    label: VerificationLabel | Literal["not_applicable"]
    """
    Document label = most severe check outcome (Portal §2.6.3); not_applicable only for self-issued documents (UI §6 enum).
    """
    issuer_sig: SignatureCheck | None
    uploader_sig: SignatureCheck | None
    checked_at: Timestamp
    response_ref: Annotated[str | None, Field(max_length=200)]
    """
    Hash or receipt of the source response; null when no source answered.
    """
    actions: list[VerificationAction]
    """
    Suggested next steps for the official (UI §7.2); the workbench has no control that runs them.
    """
    flag_count: Annotated[int, Field(ge=0)]
    checks: list[Check] | None = None
    """
    The document's VerificationResult.checks[] (Portal §2.7), for the panel's detail view.
    """
    read: ReadNote | None = None
    """
    How the file was read; the plain sentence for a scan or an unreadable file comes from it.
    """
    flags: list[Flag] | None = None
    """
    Findings raised on this document (Portal §2.6.4); additive to UI §6.4 so RB-06 can show findings no other P1 screen shows yet (e.g. UDIN).
    """


class CaseVerification(BaseModel):
    """
    RB-06 Verification panel data for one case (UI spec §6.4, §7.2): one row per document with exactly one of the six labels (or not_applicable), the two independent signature badges (§4.3) and the source checked. Advisory only; a valid uploader signature never makes a document verified (Portal §2.6.3). Demo chains are always shown as TEST TRUST ANCHOR and mock sources as MOCK SOURCE (guard rail 10).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    case_id: CaseId
    advisory: Literal[True]
    trust_anchor_label: Annotated[str, Field(max_length=64, min_length=1)]
    """
    Label of the configured trust anchor: 'TEST TRUST ANCHOR' in the demo, the CCA root in production.
    """
    last_full_run_at: Timestamp
    label_counts: Annotated[LabelCounts, Field(title="LabelCounts")]
    documents: list[CaseVerificationDocument]


class Document(BaseModel):
    """
    A document in a case (Portal spec §2.6.2). classified_type comes from body text / issuer, never heading, filename or uploader label (decision #15); when it differs from declared_type a suspected_anomaly.document_misclassified flag is raised.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    doc_id: DocId
    slot: Annotated[str, Field(max_length=120, min_length=1)]
    """
    e.g. annex2.1(i) affidavit
    """
    declared_type: Annotated[str, Field(max_length=120, min_length=1)]
    classified_type: Annotated[str | None, Field(max_length=120)]
    format_type: Annotated[FormatType, Field(title="FormatType")]
    """
    T = AICTE template, E = external, P = portal data (design B).
    """
    template_id: Annotated[str | None, Field(max_length=120)] = None
    sha256: Sha256
    bytes: Annotated[int, Field(ge=0)]
    page_count: Annotated[int, Field(ge=0)]
    received_at: Timestamp
    signatures: list[SignatureCheck]
    verification: VerificationResult | None = None
    flag_count: Annotated[int, Field(ge=0)]
