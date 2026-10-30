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
 * Portal permanent ID in printed form (design D4).
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "PermanentId".
 */
export type PermanentId = string;
/**
 * Table 2.3 route (UI spec §6).
 */
export type CaseRoute = "self_disclosure" | "scrutiny" | "scrutiny_evc" | "scrutiny_only";
/**
 * C2 stage ①–⑦.
 */
export type CaseStage = "1" | "2" | "3" | "4" | "5" | "6" | "7";
/**
 * An application category as printed in the affidavit's numbered category line, e.g. EoA Only.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "CategoryName".
 */
export type CategoryName = string;
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "DocId".
 */
export type DocId = string;
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "RunId".
 */
export type RunId = string;
/**
 * core = 19 core declarations; existing_institute = 5 'Existing Institute' declarations; extra = a block the 2024-27 draft does not print (e.g. a 2023-24-style Increase-in-Intake block).
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "DeclarationBlock".
 */
export type DeclarationBlock = "core" | "existing_institute" | "extra";
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Sha256".
 */
export type Sha256 = string;
/**
 * Where the sworn text came from: the PDF text layer, or OCR of a scanned file. Text read by OCR never decides anything.
 */
export type TextSource = "text_layer" | "ocr";
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
export type DiffOpKind = "equal" | "added" | "removed" | "changed";
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "FlagId".
 */
export type FlagId = string;
export type DiffSpanKind = "equal" | "insert" | "delete";
export type CategoryLineState = "present" | "missing" | "extra" | "different";
export type AffidavitTableName =
  "land" | "room_admin" | "room_amenities" | "room_instructional" | "room_common";
export type TableRowState = "matched" | "differs" | "missing_in_sworn" | "extra_in_sworn";
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
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Date".
 */
export type Date = string;
export type ComparisonState = "compared" | "not_compared";
/**
 * Where the sworn text came from, or why there is none.
 */
export type ComparisonSource =
  | "text_layer"
  | "scan_read"
  | "scan_unreliable"
  | "scan_not_read"
  | "scan_timeout"
  | "ocr_unavailable"
  | "unreadable";
export type ReadStatus = "native" | "ocr_read" | "blocked";
export type ConfidenceBand = "high" | "medium" | "low";
export type Provenance = "satya" | "portal";
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Severity".
 */
export type Severity = "info" | "warning" | "critical";
export type DispositionAction =
  "accept" | "override" | "escalate_clarify" | "escalate_refer" | "escalate_manual";
/**
 * Keycloak realm roles (UI spec §1).
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Role".
 */
export type Role = "RB" | "SC" | "EV" | "HC" | "RA" | "AU" | "INS";
/**
 * RFC 3339 date-time with offset (format-checked; Pydantic AwareDatetime); stored UTC, shown IST.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "Timestamp".
 */
export type Timestamp = string;
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
 * Flag only; blank in the report = unknown, never no (design D4).
 */
export type TriState = "yes" | "no" | "unknown";
export type LatitudeHemisphere = "N" | "S";
export type LongitudeHemisphere = "E" | "W";
export type VerificationAction = "recheck" | "route_manual" | "retry";
export type CheckKind =
  | "issuer_signature"
  | "uploader_signature"
  | "source_lookup"
  | "qr_consistency"
  | "expiry"
  | "format"
  | "chronology";
export type SourceMode = "live" | "mock" | "offline" | "none";
export type ExpiryBasis = "printed" | "computed_from_state_rule";
/**
 * RFC 3339 date-time with offset (format-checked; Pydantic AwareDatetime); stored UTC, shown IST.
 */
export type Timestamp1 = string;
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "CorrelationId".
 */
export type CorrelationId = string;
/**
 * T = AICTE template, E = external, P = portal data (design B).
 */
export type FormatType = "T" | "E" | "P";
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
 * RB-05 DiffView payload, GET /v1/cases/{case_id}/affidavit-diff (UI spec §6.3, §7.1; design B1 row 1, C3). M5 output: the sworn Affidavit 2 compared clause by clause with the portal draft for the same AID and AY, and its land and room tables reconciled with the ApplicationSnapshot. Advisory only. Identifier cells that the gateway tokenises (deed holder, deed document no.) are masked.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "AffidavitDiff".
 */
export interface AffidavitDiff {
  case: AffidavitCase;
  doc_id: DocId;
  run_id?: RunId;
  engine_version: string;
  ruleset_version: string;
  advisory: true;
  expected: AffidavitExpected;
  sworn: AffidavitSworn;
  normalisation: AffidavitNormalisation;
  options: DeclarationOption[];
  ops: DiffOp[];
  structure: AffidavitStructure;
  tables: AffidavitTable[];
  /**
   * Filled by the signature and stamp check from the stamp page; null when no stamp page is found.
   */
  stamp: AffidavitStamp | null;
  /**
   * Application ≤ stamp ≤ notarisation ≤ DSC ≤ upload (design B1 row 1, D1). Filled by the signature and stamp check.
   */
  chronology: AffidavitChronology | null;
  comparison?: Comparison;
  /**
   * DiffView sections whose checks belong to a later module, so the UI can say so instead of showing an empty panel.
   */
  pending: PendingSection[];
  flags: Flag[];
}
export interface AffidavitCase {
  case_id: CaseId;
  application_id: ApplicationId;
  permanent_id?: PermanentId;
  ay: AcademicYear;
  regional_office: string;
  institution_name?: string;
  route: CaseRoute;
  stage: CaseStage;
  category_set: CategoryName[];
}
/**
 * Portal-generated Affidavit 2 for this AID and AY.
 */
export interface AffidavitExpected {
  template_id: string;
  /**
   * APH edition the template belongs to, e.g. 2024-27.
   */
  template_year: string;
  aid: ApplicationId;
  category_list: CategoryName[];
  declarations: ExpectedDeclaration[];
}
export interface ExpectedDeclaration {
  /**
   * Canonical position 1–24 (core 1–19, existing institute 20–24).
   */
  no: number;
  /**
   * Number as printed in the draft; numbering restarts in the existing-institute block (design B1 row 1).
   */
  printed_no: number;
  block: DeclarationBlock;
  text: string;
}
export interface AffidavitSworn {
  page_count: number;
  sha256: Sha256;
  /**
   * The sworn copy's heading and AY line identify the expected template.
   */
  template_match: boolean;
  template_detected?: string | null;
  text_source: TextSource;
  /**
   * null for a text layer.
   */
  ocr_mean_confidence: number | null;
  /**
   * Filled by the signature check; null when it could not read the file.
   */
  issuer_sig: SignatureCheck | null;
  /**
   * Filled by the signature check; null when it could not read the file.
   */
  uploader_sig: SignatureCheck | null;
  /**
   * null when no category line was found.
   */
  category_list_found: CategoryName[] | null;
  declarations: SwornDeclaration[];
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
export interface SwornDeclaration {
  /**
   * Position in the sworn copy, counted across blocks.
   */
  no: number;
  /**
   * Number as printed in the sworn copy.
   */
  printed_no: number | null;
  block: DeclarationBlock;
  text: string;
  page: number;
  region: Region;
  ocr_confidence: number | null;
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
export interface AffidavitNormalisation {
  whitespace: boolean;
  /**
   * Struck-through spans removed before comparing.
   */
  strike_through_resolved: number;
  names_substituted: boolean;
  hyphens_rejoined: number;
  /**
   * Date order of the template year (design D4).
   */
  date_order: "MM/DD/YYYY" | "DD/MM/YYYY";
  /**
   * Dates whose month was impossible in the template order and parsed the other way.
   */
  date_order_fallbacks?: number;
}
/**
 * A strike-through option group in a declaration and the choice the deponent left standing.
 */
export interface DeclarationOption {
  decl_no: number;
  group: string;
  choices: string[];
  selected: string[];
}
export interface DiffOp {
  op: DiffOpKind;
  /**
   * Canonical expected position 1–24; null for an added declaration.
   */
  decl_no: number | null;
  /**
   * Position of the matched declaration in the sworn copy (see sworn.declarations[].no); null for a removed declaration.
   */
  sworn_no: number | null;
  similarity: number;
  flag_id?: FlagId;
  spans: DiffSpan[];
}
export interface DiffSpan {
  kind: DiffSpanKind;
  text: string;
}
export interface AffidavitStructure {
  category_line: CategoryLineCheck;
  core: BlockCount;
  existing_institute: BlockCount;
  extra_blocks: ExtraBlock[];
}
export interface CategoryLineCheck {
  expected: CategoryName[];
  found: CategoryName[];
  state: CategoryLineState;
  page?: number | null;
  flag_id?: FlagId;
}
/**
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "BlockCount".
 */
export interface BlockCount {
  expected: number;
  found: number;
}
export interface ExtraBlock {
  heading: string;
  page: number;
}
export interface AffidavitTable {
  table: AffidavitTableName;
  /**
   * Field keys in column order, e.g. area_acre; the UI translates them.
   */
  columns: string[];
  rows: AffidavitTableRow[];
  total_rows: number;
  /**
   * Land only: sum of sworn deed areas (the portal leaves the total blank).
   */
  computed_total_acres: number | null;
  /**
   * Land only: ApplicationSnapshot land.total_area in acres.
   */
  expected_total_acres: number | null;
  /**
   * Room IDs used more than once across the 4 room tables.
   */
  room_id_duplicates: string[];
}
export interface AffidavitTableRow {
  /**
   * Row key: deed row number (land) or room ID (rooms).
   */
  key: string;
  state: TableRowState;
  page?: number | null;
  region?: Region | null;
  sworn_cells: (string | null)[];
  application_report_cells: (string | null)[];
  cell_match: (boolean | null)[];
  delta?: number | null;
  flag_ids?: FlagId[];
}
export interface AffidavitStamp {
  instrument: string;
  certificate_no: string | null;
  second_party: string | null;
  /**
   * Stamp duty in paise (Portal §2 conventions).
   */
  duty: number | null;
  state: VerificationLabel;
  /**
   * Description of document on the stamp, e.g. 'Article 4 Affidavit'.
   */
  article?: string | null;
  issue_date?: Date | null;
  page?: number | null;
}
export interface AffidavitChronology {
  application_date: Date | null;
  stamp_date: Date | null;
  notary_date: Date | null;
  dsc_date?: Date | null;
  upload_date: Date | null;
  order_ok: boolean | null;
  notary_expiry?: Date | null;
  /**
   * Where dsc_date comes from: a real CMS signature or a printed mark (image only).
   */
  dsc_kind?: "signature" | "image_mark" | null;
  /**
   * A printed signature mark dated after the notarisation (design D1 review case); null when there is no mark.
   */
  mark_after_notary?: boolean | null;
  notary_expiry_ok?: boolean | null;
}
/**
 * Whether the sworn copy was really compared with the portal draft. Added by the API; the page says a copy matches only when state is compared. A scan or an unreadable file is not_compared: OCR text never decides anything.
 */
export interface Comparison {
  state: ComparisonState;
  source: ComparisonSource;
  read: ReadNote;
}
/**
 * How a file was read: the PDF text layer, OCR of a scan, or not at all. The wording of the sentence is a translated template picked by `variant`. Text read by OCR never decides anything.
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "ReadNote".
 */
export interface ReadNote {
  status: ReadStatus;
  /**
   * Short code for auditors, for example SCAN_IMAGE_ONLY. The code is shared by a scan that was read and a scan that was not.
   */
  reason_code: string | null;
  /**
   * Key of the plain sentence, for example scan_read, low_confidence, scan_not_attempted.
   */
  variant: string | null;
  /**
   * Numbers the sentence mentions (confidence, threshold, pages).
   */
  values: {
    [k: string]: string | number | undefined;
  };
  ocr_mean_confidence: number | null;
}
export interface PendingSection {
  section: "stamp" | "chronology" | "signatures" | "ocr";
  module: string;
  promise: string;
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
export interface FlagYoy {
  ay_a_ref: string;
  ay_b_ref: string;
  verdict: YoyVerdict;
}
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
 * RB-06 Verification panel data for one case (UI spec §6.4, §7.2): one row per document with exactly one of the six labels (or not_applicable), the two independent signature badges (§4.3) and the source checked. Advisory only; a valid uploader signature never makes a document verified (Portal §2.6.3). Demo chains are always shown as TEST TRUST ANCHOR and mock sources as MOCK SOURCE (guard rail 10).
 *
 * This interface was referenced by `SatyaContracts`'s JSON-Schema
 * via the `definition` "CaseVerification".
 */
export interface CaseVerification {
  case_id: CaseId;
  advisory: true;
  /**
   * Label of the configured trust anchor: 'TEST TRUST ANCHOR' in the demo, the CCA root in production.
   */
  trust_anchor_label: string;
  last_full_run_at: Timestamp;
  label_counts: LabelCounts;
  documents: CaseVerificationDocument[];
}
export interface LabelCounts {
  verified: number;
  mismatch_detected: number;
  expired: number;
  verification_pending: number;
  source_unavailable: number;
  manual_review_required: number;
}
export interface CaseVerificationDocument {
  doc_id: DocId;
  slot: string;
  title: string;
  /**
   * T = AICTE template, E = external, P = portal data (design B).
   */
  format_type: "T" | "E" | "P";
  state_code: string | null;
  /**
   * Annexure-14 issuer profile id; null when none is recorded.
   */
  issuer_profile: string | null;
  source: VerificationSource;
  /**
   * Document label = most severe check outcome (Portal §2.6.3); not_applicable only for self-issued documents (UI §6 enum).
   */
  label: VerificationLabel | "not_applicable";
  issuer_sig: SignatureCheck | null;
  uploader_sig: SignatureCheck | null;
  checked_at: Timestamp;
  /**
   * Hash or receipt of the source response; null when no source answered.
   */
  response_ref: string | null;
  /**
   * Suggested next steps for the official (UI §7.2); the workbench has no control that runs them.
   */
  actions: VerificationAction[];
  flag_count: number;
  /**
   * The document's VerificationResult.checks[] (Portal §2.7), for the panel's detail view.
   */
  checks?: Check[];
  read?: ReadNote1;
  /**
   * Findings raised on this document (Portal §2.6.4); additive to UI §6.4 so RB-06 can show findings no other P1 screen shows yet (e.g. UDIN).
   */
  flags?: Flag[];
}
export interface VerificationSource {
  /**
   * e.g. 'pdf-signature' (offline chain check), 'icai-udin', 'tn-fire-licence'.
   */
  channel: string;
  /**
   * Same values as CheckSource.mode; every mock result is shown as MOCK SOURCE.
   */
  adapter_mode: "live" | "mock" | "offline" | "none";
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
  /**
   * Links the check to the flag it raised (Flag.check_ref), e.g. m6:STAMP-CHRONO:chronology:order.
   */
  check_ref?: string;
  signed_at?: Timestamp1;
  /**
   * Signature checks: the anchor the chain built to; demo chains are always 'TEST TRUST ANCHOR' (guard rail 10).
   */
  trust_anchor_label?: string;
}
export interface CheckEvidence {
  page: number;
  regions?: Region[];
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
 * How a file was read: the PDF text layer, OCR of a scan, or not at all. The wording of the sentence is a translated template picked by `variant`. Text read by OCR never decides anything.
 */
export interface ReadNote1 {
  status: ReadStatus;
  /**
   * Short code for auditors, for example SCAN_IMAGE_ONLY. The code is shared by a scan that was read and a scan that was not.
   */
  reason_code: string | null;
  /**
   * Key of the plain sentence, for example scan_read, low_confidence, scan_not_attempted.
   */
  variant: string | null;
  /**
   * Numbers the sentence mentions (confidence, threshold, pages).
   */
  values: {
    [k: string]: string | number | undefined;
  };
  ocr_mean_confidence: number | null;
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
   * Type-specific payload (§2.4, §2.5). Per-type payload.
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
