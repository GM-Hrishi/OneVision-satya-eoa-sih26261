/* GENERATED from packages/shared-types/schemas by scripts/generate.mjs. Do not edit. */

/**
 * Academic year as printed, e.g. 2026-27.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "AcademicYear".
 */
export type AcademicYear = string;
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "AlertId".
 */
export type AlertId = string;
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "AlertType".
 */
export type AlertType =
  "missing_info" | "expired" | "pending_source" | "suspected_anomaly" | "unresolved" | "role";
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "AlertSubtype".
 */
export type AlertSubtype =
  | "document_missing"
  | "field_missing"
  | "category_line_missing"
  | "uploader_dsc_missing"
  | "document_expired"
  | "expiring_soon"
  | "partial_oc_limit_reached"
  | "signing_cert_expired"
  | "source_pending_overdue"
  | "source_unavailable"
  | "trust_anchor_revalidation"
  | "affidavit_diff"
  | "signature_integrity"
  | "signature_image_only"
  | "stamp_chronology"
  | "identity_graph"
  | "yoy_discrepancy"
  | "document_misclassified"
  | "media_reuse"
  | "flag_undisposed_overdue"
  | "manual_task_overdue"
  | "clarification_overdue"
  | "compliance_window_expiring"
  | "compliance_window_lapsed"
  | "case_assigned"
  | "sitting_scheduled"
  | "evc_scheduled"
  | "hearing_scheduled"
  | "selection_round_opened";
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Severity".
 */
export type Severity = "info" | "warning" | "critical";
/**
 * Keycloak realm roles (UI spec §1).
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Role".
 */
export type Role = "RB" | "SC" | "EV" | "HC" | "RA" | "AU" | "INS";
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "CaseId".
 */
export type CaseId = string;
/**
 * Portal application ID in printed form (design D4). Demo data uses 1-9….
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "ApplicationId".
 */
export type ApplicationId = string;
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "FlagId".
 */
export type FlagId = string;
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "DocId".
 */
export type DocId = string;
/**
 * The six PS verification labels (Portal spec §2.6.3). Document label = most severe check outcome, in x-precedence order (most severe first). `verified` also requires at least one authenticity check; a valid uploader DSC never makes a document verified.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "VerificationLabel".
 */
export type VerificationLabel =
  | "verified"
  | "mismatch_detected"
  | "expired"
  | "verification_pending"
  | "source_unavailable"
  | "manual_review_required";
/**
 * RFC 3339 date-time with offset (format-checked; Pydantic AwareDatetime); stored UTC, shown IST.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Timestamp".
 */
export type Timestamp = string;
/**
 * Portal permanent ID in printed form (design D4).
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "PermanentId".
 */
export type PermanentId = string;
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Date".
 */
export type Date = string;
/**
 * Flag only; blank in the report = unknown, never no (design D4).
 */
export type TriState = "yes" | "no" | "unknown";
export type LatitudeHemisphere = "N" | "S";
export type LongitudeHemisphere = "E" | "W";
export type CheckKind =
  | "issuer_signature"
  | "uploader_signature"
  | "source_lookup"
  | "qr_consistency"
  | "expiry"
  | "format"
  | "chronology";
export type SourceMode = "live" | "mock" | "offline" | "none";
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Sha256".
 */
export type Sha256 = string;
export type ExpiryBasis = "printed" | "computed_from_state_rule";
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "CorrelationId".
 */
export type CorrelationId = string;
export type DispositionAction =
  "accept" | "override" | "escalate_clarify" | "escalate_refer" | "escalate_manual";
/**
 * T = AICTE template, E = external, P = portal data (design B).
 */
export type FormatType = "T" | "E" | "P";
export type SignatureRole = "issuer" | "uploader";
export type SignatureState =
  | "verified"
  | "image_only"
  | "chain_broken"
  | "edited_after_signing"
  | "not_digital"
  | "not_applicable"
  | "present"
  | "absent_required";
export type DecidedBy = "system" | "official";
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "EventId".
 */
export type EventId = string;
/**
 * All inbound and outbound event types.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "EventType".
 */
export type EventType =
  | "application.precheck_requested"
  | "application.submitted"
  | "application.reopened"
  | "committee.scrutiny_constituted"
  | "committee.rescrutiny_constituted"
  | "deficiency.posted"
  | "evc.selection_round_opened"
  | "evc.selection_recorded"
  | "evc.scheduled"
  | "evc.media_submitted"
  | "hearing.scheduled"
  | "compliance.submitted"
  | "decision.recorded"
  | "eoa.letter_issued"
  | "enrolment.uploaded"
  | "faculty.record_changed"
  | "complaint.referred"
  | "precheck.completed"
  | "case.validation_completed"
  | "case.evidence_pack_ready"
  | "evc.selection_proposal_ready"
  | "evc.checklist_ready"
  | "evc.media_check_completed"
  | "case.dossier_ready"
  | "document.status_changed"
  | "alert.raised"
  | "observation.recorded"
  | "observation.withdrawn"
  | "clarification.requested"
  | "referral.recommended"
  | "deficiency.candidates_proposed"
  | "ingest.failed";
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "RunId".
 */
export type RunId = string;
export type ConfidenceBand = "high" | "medium" | "low";
export type Provenance = "satya" | "portal";
/**
 * C2 stage ①–⑦.
 */
export type Stage = "1" | "2" | "3" | "4" | "5" | "6" | "7";
/**
 * M13 year-over-year verdict (design C4a): explained by an approved application, or a discrepancy.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "YoyVerdict".
 */
export type YoyVerdict = "explained" | "discrepancy";
/**
 * Portal → SATYA (Portal spec §2.4).
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "InboundEventType".
 */
export type InboundEventType =
  | "application.precheck_requested"
  | "application.submitted"
  | "application.reopened"
  | "committee.scrutiny_constituted"
  | "committee.rescrutiny_constituted"
  | "deficiency.posted"
  | "evc.selection_round_opened"
  | "evc.selection_recorded"
  | "evc.scheduled"
  | "evc.media_submitted"
  | "hearing.scheduled"
  | "compliance.submitted"
  | "decision.recorded"
  | "eoa.letter_issued"
  | "enrolment.uploaded"
  | "faculty.record_changed"
  | "complaint.referred";
/**
 * SATYA → portal (Portal spec §2.5), all advisory.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "OutboundEventType".
 */
export type OutboundEventType =
  | "precheck.completed"
  | "case.validation_completed"
  | "case.evidence_pack_ready"
  | "evc.selection_proposal_ready"
  | "evc.checklist_ready"
  | "evc.media_check_completed"
  | "case.dossier_ready"
  | "document.status_changed"
  | "alert.raised"
  | "observation.recorded"
  | "observation.withdrawn"
  | "clarification.requested"
  | "referral.recommended"
  | "deficiency.candidates_proposed"
  | "ingest.failed";
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "ReceiptId".
 */
export type ReceiptId = string;
/**
 * Risk band (decision #20). Orders review only; never a 0–100 score; never shown to the institution.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "RiskBand".
 */
export type RiskBand = "high" | "medium" | "low";

/**
 * GENERATED from packages/shared-types/schemas by scripts/generate.mjs. Do not edit. All SATYA-EoA contracts (Portal spec §2) in one document.
 */
export interface SatyaContracts {}
/**
 * Alert with type + subtype (Portal spec §2.9). Institution-facing alerts are limited to missing_info, expired, unresolved.clarification_* and unresolved.compliance_window_*.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Alert".
 */
export interface Alert {
  alert_id: AlertId;
  type: AlertType;
  subtype: AlertSubtype;
  severity: Severity;
  /**
   * @minItems 1
   */
  audience_roles: [Role, ...Role[]];
  case_id: CaseId;
  application_id: ApplicationId;
  flag_id?: FlagId;
  doc_id?: DocId;
  label?: VerificationLabel;
  aph_clause?: string;
  text_key: string;
  due_at?: Timestamp;
  created_at: Timestamp;
  read: boolean;
}
/**
 * The Application Report field set as the portal sends it (Portal spec §2.6.1). Every property carries x-handling: K keep, T tokenise (keyed HMAC-SHA256, key never stored with the data), R result only (portal's computed value, D2). Fields marked X must not be sent and do not exist in this model; they are listed in x-rejected-fields and the gateway answers PERSONAL_DATA_REJECTED. Unknown fields are rejected (additionalProperties false) for data minimisation.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "ApplicationSnapshot".
 */
export interface ApplicationSnapshot {
  ay: AcademicYear;
  captured_at?: Timestamp;
  basic: SnapshotBasic;
  trust?: SnapshotTrust;
  trustees?: SnapshotTrustee[];
  authorised_signatory?: SnapshotSignatory;
  courses?: SnapshotCourse[];
  land?: SnapshotLand;
  buildings?: SnapshotBuilding[];
  rooms?: SnapshotRooms;
  facilities?: PrintedSection;
  committees?: PrintedSection;
  bank?: SnapshotBank;
  finance?: SnapshotFinance;
  declaration?: SnapshotDeclaration;
  faculty?: SnapshotFaculty[];
  deficiency_report?: DeficiencyReportResult;
}
export interface SnapshotBasic {
  application_id: ApplicationId;
  permanent_id?: PermanentId;
  institution_type?: string;
  status?: string;
  application_date?: Date;
  submission_date?: Date | null;
  regional_office: string;
  overall_deficiency: TriState;
}
export interface SnapshotTrust {
  name: string;
  registration_ref?: string;
}
export interface SnapshotTrustee {
  /**
   * Trustee name. Tokenised at the gateway (keyed HMAC-SHA256) before anything is stored; stored as trustee_token.
   */
  name: string;
  role: string;
  tenure_from?: Date;
  tenure_to?: Date | null;
}
export interface SnapshotSignatory {
  /**
   * Chairman/Secretary name, used only for the M6 signer check (§2.8). Tokenised at the gateway (keyed HMAC-SHA256) before anything is stored; stored as signatory_token.
   */
  name: string;
  designation: "chairman" | "secretary" | "authorised_person";
}
export interface SnapshotCourse {
  programme: string;
  level: string;
  course: string;
  /**
   * Intake approved for the last 2 AYs.
   *
   * @maxItems 2
   */
  intake_approved?: [] | [ApprovedIntake] | [ApprovedIntake, ApprovedIntake];
  intake_applied: number;
  faculty_required?: number;
  faculty_actual?: number;
  nri_status?: string;
  international_students_status?: string;
  nba_status?: string;
}
export interface ApprovedIntake {
  ay: AcademicYear;
  intake: number;
}
export interface SnapshotLand {
  total_area?: number;
  unit?: "acre" | "hectare" | "sq_m";
  pieces?: number;
  max_distance_km?: number;
  land_use_certificate_issuer?: string;
  land_use_certificate_date?: Date;
  coordinates?: CoordinatesDms;
  deeds?: SnapshotDeed[];
}
export interface CoordinatesDms {
  lat: LatitudeDms;
  lon: LongitudeDms;
}
export interface LatitudeDms {
  deg: number;
  min: number;
  sec: number;
  hemisphere: LatitudeHemisphere;
}
export interface LongitudeDms {
  deg: number;
  min: number;
  sec: number;
  hemisphere: LongitudeHemisphere;
}
export interface SnapshotDeed {
  /**
   * Deed holder. Tokenised at the gateway (keyed HMAC-SHA256) before anything is stored; stored as holder_token.
   */
  holder: string;
  /**
   * Deed document number. Tokenised at the gateway (keyed HMAC-SHA256) before anything is stored; stored as deed_token.
   */
  document_no: string;
  registration_date?: Date;
  plot_no?: string;
  village_district?: string;
  area_acre: number;
}
export interface SnapshotBuilding {
  block: string;
  sanctioned_area_m2?: number;
  constructed_area_m2?: number;
  approving_authority?: string;
  approval_date?: Date;
}
export interface SnapshotRooms {
  administrative?: RoomRow[];
  amenities?: RoomRow[];
  instructional?: RoomRow[];
  instructional_common?: RoomRow[];
}
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "RoomRow".
 */
export interface RoomRow {
  room_id: string;
  room_type: string;
  carpet_area_m2: number;
  /**
   * Completion of flooring, as printed (e.g. Ready).
   */
  flooring?: string;
  walls_painting?: string;
  electrification?: string;
}
/**
 * Portal-computed section kept as printed, display only (D2).
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "PrintedSection".
 */
export interface PrintedSection {
  items?: PrintedItem[];
}
export interface PrintedItem {
  name: string;
  value: string;
}
/**
 * Account number is X (rejected), never part of this model.
 */
export interface SnapshotBank {
  bank_name?: string;
  ifsc?: string;
}
export interface SnapshotFinance {
  fy?: string;
  income_total_paise?: number;
  expenditure_total_paise?: number;
  heads?: FinanceHead[];
}
export interface FinanceHead {
  head: string;
  income_paise?: number;
  expenditure_paise?: number;
}
export interface SnapshotDeclaration {
  items?: DeclarationItems;
  category_list?: string[];
}
export interface DeclarationItems {
  a?: boolean;
  b?: boolean;
  c?: boolean;
  d?: boolean;
  e?: boolean;
  f?: boolean;
}
export interface SnapshotFaculty {
  /**
   * Portal Faculty ID (1- + 9–11 digits). Reveal only via a logged official action (AU-04). Tokenised at the gateway (keyed HMAC-SHA256) before anything is stored; stored as faculty_token.
   */
  faculty_id: string;
  designation: string;
  appointment_type?: string;
  programme?: string;
  department?: string;
  date_of_joining?: Date;
  highest_qualification_level?: string;
  relieved_date?: Date | null;
  /**
   * Portal's own within-portal duplicate flag (D2); never recomputed.
   */
  is_duplicate?: boolean;
  /**
   * Portal's PAN validation result only (D2); the PAN itself is X.
   */
  pan_validation?: string;
  record_status?: string;
}
/**
 * Portal Deficiency Report result, imported not recomputed (D2, guard rail 8).
 */
export interface DeficiencyReportResult {
  template_year?: string;
  sections?: DeficiencySection[];
  overall: "yes" | "no" | "unknown";
  /**
   * The only HOI-derived value SATYA keeps (HOI personal details are X).
   */
  principal_eligibility?: "yes" | "no" | "unknown";
}
export interface DeficiencySection {
  section: string;
  deficiency: "yes" | "no";
}
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Check".
 */
export interface Check {
  kind: CheckKind;
  outcome: VerificationLabel;
  reason_code: string;
  evidence?: CheckEvidence;
  source?: CheckSource;
  checked_at?: Timestamp;
  response_sha256?: Sha256;
  attempts?: number;
  /**
   * Drives mismatch_detected.
   */
  field_diff?: FieldDiff[];
  valid_from?: Date;
  valid_to?: Date;
  basis?: ExpiryBasis;
}
export interface CheckEvidence {
  page: number;
  regions?: Region[];
}
/**
 * Evidence region on a page, normalised 0–1.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Region".
 */
export interface Region {
  x: number;
  y: number;
  w: number;
  h: number;
}
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "CheckSource".
 */
export interface CheckSource {
  adapter_id: string;
  mode: SourceMode;
  name: string;
}
export interface FieldDiff {
  field: string;
  submitted: string | number | boolean | null;
  source: string | number | boolean | null;
}
/**
 * An official's recorded decision on a flag (Portal spec §2.6.5; UI spec §4.2). No action changes regulatory status; undo is a new ledger entry.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Disposition".
 */
export interface Disposition {
  action: DispositionAction;
  reason: string;
  reason_template_id?: string;
  /**
   * Opaque user reference (Keycloak subject), never a name.
   */
  by_user_ref: string;
  by_role: Role;
  at: Timestamp;
  ledger_no: number;
}
/**
 * A document in a case (Portal spec §2.6.2). classified_type comes from body text / issuer, never heading, filename or uploader label (decision #15); when it differs from declared_type a suspected_anomaly.document_misclassified flag is raised.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Document".
 */
export interface Document {
  doc_id: DocId;
  /**
   * e.g. annex2.1(i) affidavit
   */
  slot: string;
  declared_type: string;
  classified_type: string | null;
  format_type: FormatType;
  template_id?: string | null;
  sha256: Sha256;
  bytes: number;
  page_count: number;
  received_at: Timestamp;
  signatures: SignatureCheck[];
  verification?: VerificationResult;
  flag_count: number;
}
/**
 * One of the two independent signature checks (Portal spec §2.8, UI spec §4.3). An image-only mark is never verified (decision #16).
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "SignatureCheck".
 */
export interface SignatureCheck {
  role: SignatureRole;
  state: SignatureState;
  /**
   * true only for a real CMS signature (/ByteRange).
   */
  has_byte_range: boolean;
  reason_code?: string;
  page?: number;
  signer_role?: "chairman" | "secretary" | "issuer" | "unknown";
  /**
   * Demo chain anchors are always 'TEST TRUST ANCHOR' (guard rail 10).
   */
  trust_anchor_label?: string;
}
/**
 * Per-document verification with all checks (Portal spec §2.7). Every mock result is shown as MOCK SOURCE (guard rail 10).
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "VerificationResult".
 */
export interface VerificationResult {
  doc_id: DocId;
  label: VerificationLabel;
  decided_by: DecidedBy;
  /**
   * Required when an official resolves the label.
   */
  basis_note?: string;
  checks: Check[];
}
/**
 * Event envelope for both directions (Portal spec §2.3). Every inbound type is a proposed hook that the mock portal implements (guard rail 2). Outbound events must carry advisory: true and regulatory_effect: none (guard rail 1). Consumers ignore unknown top-level fields (§2.12).
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "EventEnvelope".
 */
export interface EventEnvelope {
  spec: "satya.event/1";
  event_id: EventId;
  type: EventType;
  occurred_at: Timestamp;
  /**
   * e.g. mock-portal, satya
   */
  producer: string;
  subject: Subject;
  /**
   * Per application, increases by 1.
   */
  sequence: number;
  correlation_id: CorrelationId;
  /**
   * Type-specific payload (§2.4, §2.5). Per-type schemas arrive with their slices.
   */
  data: {};
  advisory?: true;
  regulatory_effect?: "none";
  case_id?: CaseId;
  run_id?: RunId;
  /**
   * Opaque path; no personal data, no tokens.
   */
  deep_link?: string;
}
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Subject".
 */
export interface Subject {
  application_id: ApplicationId;
  permanent_id?: PermanentId;
  ay: AcademicYear;
}
/**
 * An evidence-linked finding (Portal spec §2.6.4). Every flag cites rule_id + rule_version + aph_clause + aph_edition (guard rail 6). Anomaly/forgery-type flags carry preliminary_indicator: true (PS FR2).
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Flag".
 */
export interface Flag {
  flag_id: FlagId;
  /**
   * null for snapshot-level findings.
   */
  doc_id: DocId | null;
  page: number | null;
  regions: Region[];
  rule_id: string;
  rule_version: string;
  rule_text_key: string;
  aph_clause: string;
  /**
   * e.g. 2024-27
   */
  aph_edition: string;
  extracted_value: string | number | boolean | null;
  expected_value: string | number | boolean | null;
  value_unit: string | null;
  delta?: number | null;
  extracted_source: ExtractedSource;
  expected_source: ExpectedSource;
  confidence: number;
  confidence_band: ConfidenceBand;
  label: VerificationLabel;
  provenance: Provenance;
  preliminary_indicator: boolean;
  severity: Severity;
  disposition: Disposition | null;
  check_ref?: string;
  stage: Stage;
  institution_visible: boolean;
  yoy?: FlagYoy;
  evidence_sha256: Sha256;
}
export interface ExtractedSource {
  doc_label: string;
  page: number | null;
  row?: string | number | null;
}
export interface ExpectedSource {
  label: string;
}
export interface FlagYoy {
  ay_a_ref: string;
  ay_b_ref: string;
  verdict: YoyVerdict;
}
