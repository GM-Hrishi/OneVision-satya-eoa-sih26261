// Chain status adapter (footer chip and Audit page). Pure: turns whichever answer the API gave into one
// view-model. Honest rule: the status comes only from a recomputation by the API (GET /v1/audit/verify on
// the backend branch, or the `chain` block of GET /v1/audit on main). Anything else is "unknown" and the
// chip is hidden.
export type ChainState = "intact" | "broken" | "unknown";

export interface ChainStatus {
  state: ChainState;
  entries: number | null;
  firstBadEntry: number | null;
  checkedAt: string | null;
  source: "verify" | "audit";
}

const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null;
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const str = (v: unknown): string | null => (typeof v === "string" ? v : null);

/** GET /v1/audit/verify: {status: "intact"|"broken", checked_at, entries, first_bad_entry}. NOT ON MAIN UNTIL PR #15 MERGES. */
export function fromVerify(body: unknown): ChainStatus | null {
  if (!isRecord(body)) return null;
  const status = body.status;
  if (status !== "intact" && status !== "broken") return null;
  return { state: status, entries: num(body.entries), firstBadEntry: num(body.first_bad_entry), checkedAt: str(body.checked_at), source: "verify" };
}

/** GET /v1/audit on main: {chain: {ok, rows, broken_at, recomputed_at}}. */
export function fromAudit(body: unknown): ChainStatus | null {
  if (!isRecord(body) || !isRecord(body.chain)) return null;
  const c = body.chain;
  if (typeof c.ok !== "boolean") return null;
  return { state: c.ok ? "intact" : "broken", entries: num(c.rows), firstBadEntry: num(c.broken_at), checkedAt: str(c.recomputed_at), source: "audit" };
}
