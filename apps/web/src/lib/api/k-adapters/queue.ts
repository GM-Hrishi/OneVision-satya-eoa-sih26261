// View-model helpers for queue rows (overview, queue, timeline). Pure and tested.
// The cases list has no "days waiting" field: waiting days are derived from `submitted_at` against the
// overview `as_of` (or any reference time the caller passes). This is a display aid only; position or
// size never implies decision order.
import type { VerificationLabel } from "@satya/shared-types";
import type { QueueRow } from "@/lib/demo-types";
import { LABEL_ORDER } from "@/lib/labels";
import { whySummary } from "./pending-fields";

const DAY_MS = 86_400_000;

/** Whole days between submission and `asOf`, never negative; null when either time is not a date. */
export function waitingDays(submittedAt: string, asOf: string): number | null {
  const a = Date.parse(submittedAt);
  const b = Date.parse(asOf);
  if (Number.isNaN(a) || Number.isNaN(b)) return null;
  return Math.max(0, Math.floor((b - a) / DAY_MS));
}

/** Files that still wait for a person: everything except those where every finding has a decision. */
export function waitingRows(rows: readonly QueueRow[]): QueueRow[] {
  return rows.filter((r) => r.status !== "all_flags_decided");
}

/** One plain sentence for a row: why_summary when the API sends it, else the top reason's own sentence. */
export function rowSentence(row: QueueRow): string | null {
  return whySummary(row)[0] ?? row.top_reasons[0]?.short_text ?? null;
}

/** The most severe document label with a non-zero count, or null for a row with no documents. */
export function worstLabel(counts: Record<VerificationLabel, number>): VerificationLabel | null {
  return LABEL_ORDER.find((l) => (counts[l] ?? 0) > 0) ?? null;
}

export function longestWait(rows: readonly QueueRow[], asOf: string): number | null {
  const days = rows.map((r) => waitingDays(r.submitted_at, asOf)).filter((d): d is number => d !== null);
  return days.length === 0 ? null : Math.max(...days);
}
