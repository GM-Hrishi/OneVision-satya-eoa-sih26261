// VISUAL 5: replay diff. Shape: GET /v1/cases/{id}/replay-check (NOT ON MAIN UNTIL PR #15 MERGES), see
// docs/API-NOTES.md on feat/logic-rival-parity. Strict: a body that does not have the documented shape is
// treated as "not available", never repaired or guessed.
export interface ReplayRow {
  key: "findings" | "ruleset" | "as_of";
  original: string;
  replayed: string;
  same: boolean;
}
export interface ReplayVM {
  caseId: string | null;
  reproduced: boolean;
  rows: ReplayRow[];
  reasons: string[];
}

const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null;
const str = (v: unknown): string | null => (typeof v === "string" && v.length > 0 ? v : null);

export function fromReplayCheck(body: unknown): ReplayVM | null {
  if (!isRecord(body) || typeof body.reproduced_identically !== "boolean") return null;
  const original = str(body.digest_original);
  const replayed = str(body.digest_replayed);
  const rulesetId = str(body.ruleset_id);
  const asOf = str(body.as_of);
  const rows: ReplayRow[] = [];
  if (original && replayed) rows.push({ key: "findings", original, replayed, same: original === replayed });
  // The replay runs the ORIGINAL rule pack at the original time, so these two inputs are the same on both sides by construction.
  if (rulesetId) rows.push({ key: "ruleset", original: rulesetId, replayed: rulesetId, same: true });
  if (asOf) rows.push({ key: "as_of", original: asOf, replayed: asOf, same: true });
  const reasons = Array.isArray(body.reasons) ? body.reasons.filter((r): r is string => typeof r === "string") : [];
  // The headline can only say "reproduced" when the API says so AND both digests exist and match.
  const reproduced = body.reproduced_identically === true && original !== null && original === replayed;
  return { caseId: str(body.case_id), reproduced, rows, reasons };
}
