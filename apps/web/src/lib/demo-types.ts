// Slice D (demo flow) types and constants (safe to import from client components): queue, case review, alerts and audit from the Workbench API. Types are
// local because these views are demo-flow shapes, not Portal contracts. Advisory only.
import type { Flag, SignatureCheck, VerificationLabel } from "@satya/shared-types";

export type Band = "high" | "medium" | "low";
export type Status = "awaiting_review" | "in_review" | "reviewed" | "no_findings";
export const BANDS: readonly Band[] = ["high", "medium", "low"];
export const STATUSES: readonly Status[] = ["awaiting_review", "in_review", "reviewed", "no_findings"];
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

export interface AlertItem {
  case_id: string;
  application_id: string;
  type: string;
  subtype: string;
  text: string;
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

