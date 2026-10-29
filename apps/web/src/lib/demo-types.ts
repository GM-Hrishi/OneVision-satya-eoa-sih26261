// Slice D (demo flow) types and constants (safe to import from client components): queue, case review, alerts and audit from the Workbench API. Types are
// local because these views are demo-flow shapes, not Portal contracts. Advisory only.
import type { Flag, SignatureCheck, VerificationLabel } from "@satya/shared-types";

export type Band = "high" | "medium" | "low";
export type Status = "not_started" | "in_review" | "waiting_on_institution" | "referred" | "all_flags_decided";
export const BANDS: readonly Band[] = ["high", "medium", "low"];
export const STATUSES: readonly Status[] = ["not_started", "in_review", "waiting_on_institution", "referred", "all_flags_decided"];
export type SortKey = "application_id" | "undisposed_flags" | "submitted_at" | "last_activity_at";
export const SORT_KEYS: readonly SortKey[] = ["application_id", "undisposed_flags", "submitted_at", "last_activity_at"];
export type SortDir = "asc" | "desc";
export const ACTIONS = ["accept", "override", "escalate_clarify", "escalate_refer", "escalate_manual"] as const;
export type Action = (typeof ACTIONS)[number];

export interface QueueRow {
  case_id: string;
  application_id: string;
  region: string;
  ay: string;
  route: string;
  stage: string;
  institution_name: string | null;
  open_flags: number;
  undisposed_flags: number;
  risk_band: Band;
  top_reasons: { flag_id: string; rule_id: string; aph_clause: string | null; short_text: string }[];
  label_counts: Record<VerificationLabel, number>;
  status: Status;
  manual_tasks: number;
  submitted_at: string;
  last_activity_at: string;
}

export interface Disposition {
  action: Action;
  reason: string;
  by_role: string;
  at: string;
  ledger_no: number;
}

export type ReviewFlag = Flag & { why: string; doc_title: string; disposition: Disposition | null };

export interface ReviewCheck {
  kind: string;
  outcome: VerificationLabel;
  reason_code: string;
  source?: { adapter_id: string; mode: string; name: string };
  response_sha256?: string;
  checked_at?: string;
}

export interface ReadSummary {
  status: "native" | "ocr_read" | "blocked";
  reason_code: "SCAN_IMAGE_ONLY" | "OCR_LOW_CONFIDENCE" | "OCR_UNAVAILABLE" | "DOC_UNREADABLE" | null;
  variant: string | null;
  why: string | null;
  values: Record<string, string | number>;
  page_count: number;
  ocr_mean_confidence: number | null;
  pages: { page: number; kind: string; chars: number; ocr_confidence?: number; ocr_words?: number; note?: string }[];
}

export interface ReviewDocument {
  doc_id: string;
  slot: string;
  title: string;
  sha256: string;
  bytes: number | null;
  label: VerificationLabel;
  source: { channel: string; adapter_mode: string };
  issuer_sig: SignatureCheck | null;
  uploader_sig: SignatureCheck | null;
  checks: ReviewCheck[];
  manual_task: boolean;
  read: ReadSummary;
  checked_at: string;
}

export interface Review {
  case_id: string;
  documents: ReviewDocument[];
  flags: ReviewFlag[];
  tasks: { doc_id: string; title: string; reason: string }[];
  label_counts: Record<VerificationLabel, number>;
  checked_at: string;
  risk: { band: Band; reasons: QueueRow["top_reasons"]; note: string };
  status: Status;
  undisposed_flags: number;
}

export type AlertSeverity = "critical" | "warning" | "info";

export interface AlertItem {
  case_id: string;
  application_id: string;
  type: string;
  subtype: string;
  severity: AlertSeverity;
  text: string;
  created_at: string;
  alert_key: string;
  doc_id: string | null;
  label: VerificationLabel | null;
  flag_id: string | null;
  aph_clause: string | null;
  source: { mode: string } | null;
}

export interface AuditEntry {
  seq: number;
  at: string;
  event_type: string;
  case_id: string | null;
  actor: string | null;
  hash: string;
  payload_sha256: string;
  detail: Record<string, unknown> | null;
}

export interface Audit {
  chain: { ok: boolean; rows: number; broken_at: number | null; reason: string | null; recomputed_at: string; method: string };
  entries: AuditEntry[];
}


export interface Overview {
  as_of: string;
  ay: string;
  region: string | null;
  route: "self_disclosure";
  cases: { submitted: number; by_band: Record<Band, number> };
  status: Record<Status, number>;
  documents: { total: number; by_label: Record<VerificationLabel, number> };
  manual_tasks: {
    open: number;
    oldest_age_days: number;
    top: { case_id: string; application_id: string; reason_key: string; age_days: number }[];
  };
  expiring: {
    d30: number;
    d60: number;
    d90: number;
    top: { doc_type: string; doc_title: string; case_id: string; application_id: string; valid_to: string; days_left: number }[];
  };
  recent_decisions: { at: string; case_id: string; application_id: string; flag_id: string; action: Action; by_role: string; ledger_no: number }[];
  sources: { adapter_id: string; name_key: string; mode: "mock" | "offline" | "live" | "none"; status: "answering" | "unavailable" }[];
}
