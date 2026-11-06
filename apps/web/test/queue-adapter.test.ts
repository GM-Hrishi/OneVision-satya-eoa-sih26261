import { describe, expect, it } from "vitest";
import type { QueueRow } from "../src/lib/demo-types";
import { longestWait, rowSentence, waitingDays, waitingRows, worstLabel } from "../src/lib/api/k-adapters/queue";

// Row values copied from the queue-row example in docs/API-NOTES.md (feat/logic-rival-parity).
const row = {
  application_id: "1-90000004217", case_id: "cas_01JD3M5A00000000000000DT03", risk_band: "high", status: "not_started",
  submitted_at: "2026-11-06T09:00:00+00:00",
  label_counts: { expired: 0, manual_review_required: 1, mismatch_detected: 0, source_unavailable: 1, verification_pending: 0, verified: 0 },
  top_reasons: [{ flag_id: "f", rule_id: "AFF-CAT-LINE", aph_clause: "Affidavit-2 NOTE", short_text: "The numbered category line of the portal draft is missing from the sworn copy." }],
} as unknown as QueueRow;

describe("queue adapter", () => {
  it("counts whole waiting days from submission and never goes negative", () => {
    expect(waitingDays("2026-11-01T09:00:00+00:00", "2026-11-06T09:00:00+00:00")).toBe(5);
    expect(waitingDays("2026-11-06T10:00:00+00:00", "2026-11-06T09:00:00+00:00")).toBe(0);
    expect(waitingDays("2026-11-07T10:00:00+00:00", "2026-11-06T09:00:00+00:00")).toBe(0);
    expect(waitingDays("not a date", "2026-11-06T09:00:00+00:00")).toBeNull();
  });

  it("the longest wait ignores unreadable dates", () => {
    const rows = [row, { ...row, submitted_at: "2026-10-30T09:00:00+00:00" }, { ...row, submitted_at: "x" }] as QueueRow[];
    expect(longestWait(rows, "2026-11-06T09:00:00+00:00")).toBe(7);
    expect(longestWait([], "2026-11-06T09:00:00+00:00")).toBeNull();
  });

  it("files where every finding has a decision are not waiting", () => {
    expect(waitingRows([row, { ...row, status: "all_flags_decided" } as QueueRow]).length).toBe(1);
  });

  it("the row sentence prefers why_summary and falls back to the top reason", () => {
    expect(rowSentence(row)).toContain("category line");
    expect(rowSentence({ ...row, why_summary: ["From the summary."] } as unknown as QueueRow)).toBe("From the summary.");
    expect(rowSentence({ ...row, top_reasons: [] } as QueueRow)).toBeNull();
  });

  it("worst label is the most severe one with a count", () => {
    expect(worstLabel(row.label_counts)).toBe("manual_review_required");
    expect(worstLabel({ ...row.label_counts, manual_review_required: 0, source_unavailable: 0 })).toBeNull();
  });
});
