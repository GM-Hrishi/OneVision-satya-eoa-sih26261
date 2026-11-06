// Typed accessors for fields that exist on the backend branch (draft PR #15) but not in the generated shared
// types on main. Components never cast; they call these. After the merge and `make gen-types`, delete this
// file and read the fields directly (docs/ui-style-k/MERGE-NOTES.md). Shapes: docs/API-NOTES.md on that branch.
import type { ReviewFlag } from "@/lib/demo-types";

export interface Limitation {
  key: string;
  text: string;
}
export interface WhyDetail {
  key: string;
  params: Record<string, string>;
  text: string;
}
interface PendingFlag {
  limitation?: Limitation | null;
  why_detail?: WhyDetail | null;
  check_kind?: string | null;
}
interface PendingWhySummary {
  why_summary?: string[] | null;
}

const nonEmpty = (v: unknown): v is string => typeof v === "string" && v.trim().length > 0;

/** The plain "why" sentence: why_detail.text when the API sends it, else the existing `why` string (unchanged). */
export function whyText(flag: ReviewFlag): string {
  const detail = (flag as ReviewFlag & PendingFlag).why_detail?.text;
  return nonEmpty(detail) ? detail : flag.why;
}

/** "What this does not prove" text from the API. null when the flag carries none (the note is then hidden). */
export function limitationText(flag: ReviewFlag): string | null {
  const text = (flag as ReviewFlag & PendingFlag).limitation?.text;
  return nonEmpty(text) ? text : null;
}

/** Commodity PDF indicators (annotation, font, cover box, glyph overlap, AI-reader text). */
export function isHeuristic(flag: ReviewFlag): boolean {
  return (flag as ReviewFlag & PendingFlag).check_kind === "heuristic";
}

/** Up to three one-sentence summaries on a review or queue row; empty when the API does not send them. */
export function whySummary(row: object): string[] {
  const list = (row as PendingWhySummary).why_summary;
  return Array.isArray(list) ? list.filter(nonEmpty).slice(0, 3) : [];
}
