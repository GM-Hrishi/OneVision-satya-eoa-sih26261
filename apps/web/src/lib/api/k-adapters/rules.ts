// Rules adapters (read only). The rule list endpoint does not exist on main, so the list page shows the rules that
// raised a finding on queue rows (rule id, clause and the finding's own sentence). Rule detail is
// GET /v1/rules/{rule_id}: NOT ON MAIN UNTIL PR #15 MERGES; shape from docs/API-NOTES.md on that branch.
import type { QueueRow } from "@/lib/demo-types";

export interface SeenRule {
  ruleId: string;
  clause: string | null;
  sentence: string;
}

/** Distinct rules named by the top reasons of queue rows, in first-seen order. */
export function seenRules(rows: readonly QueueRow[]): SeenRule[] {
  const seen = new Map<string, SeenRule>();
  for (const row of rows) {
    for (const r of row.top_reasons) {
      if (!seen.has(r.rule_id)) seen.set(r.rule_id, { ruleId: r.rule_id, clause: r.aph_clause, sentence: r.short_text });
    }
  }
  return [...seen.values()];
}

export interface RuleDetailVM {
  ruleId: string;
  version: string | null;
  clause: string | null;
  edition: string | null;
  severity: "info" | "warning" | "critical" | null;
  label: "verified" | "mismatch_detected" | "expired" | "verification_pending" | "source_unavailable" | "manual_review_required" | null;
  limitation: string | null;
}

const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null;
const str = (v: unknown): string | null => (typeof v === "string" && v.length > 0 ? v : null);
const LABELS = ["verified", "mismatch_detected", "expired", "verification_pending", "source_unavailable", "manual_review_required"] as const;
const SEVERITIES = ["info", "warning", "critical"] as const;

export function fromRuleDetail(body: unknown): RuleDetailVM | null {
  if (!isRecord(body)) return null;
  const ruleId = str(body.rule_id);
  if (!ruleId) return null;
  const label = LABELS.find((l) => l === body.label) ?? null;
  const severity = SEVERITIES.find((s) => s === body.severity) ?? null;
  const lim = isRecord(body.limitation) ? str(body.limitation.text) : null;
  return { ruleId, version: str(body.rule_version), clause: str(body.aph_clause), edition: str(body.aph_edition), severity, label, limitation: lim };
}
