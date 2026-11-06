// View-models for the affidavit page: the summary numbers and the tie-line rows. Pure and tested.
// B-43 rule: a declaration is called a match only when the sworn copy was really compared (a text layer, state
// "compared"). A scan or an unreadable file is "not compared" throughout, never "match".
import type { AffidavitDiff, DiffOp } from "@satya/shared-types";

export interface AffidavitSummaryVM {
  total: number;
  match: number;
  differ: number;
  missing: number;
  notComparable: number;
  source: "api" | "counted";
}

const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null;
const int = (v: unknown): number | null => (typeof v === "number" && Number.isInteger(v) && v >= 0 ? v : null);

/** `summary` on affidavit-diff is NOT ON MAIN UNTIL PR #15 MERGES; read it through this accessor only. */
function apiSummary(diff: AffidavitDiff): AffidavitSummaryVM | null {
  const s = (diff as AffidavitDiff & { summary?: unknown }).summary;
  if (!isRecord(s)) return null;
  const [total, match, differ, missing, notComparable] = [int(s.total), int(s.match), int(s.differ), int(s.missing_in_sworn), int(s.not_comparable)];
  if (total === null || match === null || differ === null || missing === null || notComparable === null) return null;
  return { total, match, differ, missing, notComparable, source: "api" };
}

export function wasCompared(diff: AffidavitDiff): boolean {
  return diff.comparison?.state === "compared";
}

/** The API's summary when present, else counted from `ops` (the declarations the portal form prints). */
export function affidavitSummary(diff: AffidavitDiff): AffidavitSummaryVM {
  const fromApi = apiSummary(diff);
  if (fromApi) return fromApi;
  const total = diff.expected.declarations.length;
  if (!wasCompared(diff)) return { total, match: 0, differ: 0, missing: 0, notComparable: total, source: "counted" };
  const printed = diff.ops.filter((o) => o.decl_no !== null);
  return {
    total,
    match: printed.filter((o) => o.op === "equal").length,
    differ: printed.filter((o) => o.op === "changed").length,
    missing: printed.filter((o) => o.op === "removed").length,
    notComparable: 0,
    source: "counted",
  };
}

export interface TieRow {
  key: string;
  no: number;
  op: DiffOp["op"];
  /** Sworn copy text (left), null when the declaration is missing there. */
  sworn: string | null;
  /** Portal form text (right), null for a declaration only in the sworn copy. */
  portal: string | null;
  /** Page of the sworn copy, when known. */
  swornPage: number | null;
}

/** One row per op, in the order the API gives them. Text is the API's own; nothing is summarised here. */
export function tieRows(diff: AffidavitDiff): TieRow[] {
  const expected = new Map(diff.expected.declarations.map((d) => [d.no, d]));
  const sworn = new Map(diff.sworn.declarations.map((d) => [d.no, d]));
  return diff.ops.map((op, i) => {
    const e = op.decl_no === null ? undefined : expected.get(op.decl_no);
    const s = op.sworn_no === null ? undefined : sworn.get(op.sworn_no);
    return {
      key: `${op.decl_no ?? "x"}-${op.sworn_no ?? "x"}-${i}`,
      no: op.decl_no ?? op.sworn_no ?? i + 1,
      op: op.op,
      sworn: s?.text ?? null,
      portal: e?.text ?? null,
      swornPage: s?.page ?? null,
    };
  });
}
