// View-model for the case page (style K). Pure functions: no fetching, no UI. Components receive this.
// Nothing here invents data: every state comes from the review payload; where the payload cannot say, the
// cell is "na" (not applicable) or "check" (a person must check), never a guess.
import type { VerificationLabel } from "@satya/shared-types";
import { LABEL_ORDER } from "@/lib/labels";
import type { Review, ReviewDocument, ReviewFlag } from "@/lib/demo-types";
import { isHeuristic, limitationText, whySummary, whyText } from "./pending-fields";

export type LadderState = "agrees" | "disagrees" | "waiting" | "check" | "na";
export const LADDER_COLUMNS = ["declared", "read", "portal", "issuer", "signature"] as const;
export type LadderColumn = (typeof LADDER_COLUMNS)[number];

export interface FindingVM {
  /** 1-based pin number, in review order. */
  n: number;
  flag: ReviewFlag;
  why: string;
  limitation: string | null;
  heuristic: boolean;
  aiReader: boolean;
  /** The two clashing values, shown huge, only when both exist and are short. */
  values: { left: string; leftSource: string; right: string; rightSource: string; unit: string | null } | null;
}

export interface LadderRow {
  docId: string;
  title: string;
  label: VerificationLabel;
  cells: Record<LadderColumn, LadderState>;
  /** First finding's plain sentence on this document, or null (the label sentence is used). */
  verdictText: string | null;
}

export interface CaseView {
  findings: FindingVM[];
  ladder: LadderRow[];
  /** Findings that are not commodity indicators and are labelled mismatch or expired. */
  disagreeCount: number;
  /** Findings still needing a person's look (everything else open). */
  lookCount: number;
  lead: string | null;
}

const SEVERITY_RANK = { critical: 0, warning: 1, info: 2 } as const;
const LABEL_RANK = new Map<VerificationLabel, number>(LABEL_ORDER.map((l, i) => [l, i]));
const MAX_BIG = 10;

const shortValue = (v: unknown): string | null => {
  if (v === null || v === undefined || typeof v === "object") return null;
  const s = String(v);
  return s.length > 0 && s.length <= MAX_BIG ? s : null;
};

/** Most severe first, mismatch before manual review, commodity indicators last at equal severity. Stable. */
export function orderFlags(flags: readonly ReviewFlag[]): ReviewFlag[] {
  return flags
    .map((f, i) => ({ f, i }))
    .sort((a, b) => {
      const d =
        SEVERITY_RANK[a.f.severity] - SEVERITY_RANK[b.f.severity] ||
        Number(isHeuristic(a.f)) - Number(isHeuristic(b.f)) ||
        (LABEL_RANK.get(a.f.label) ?? 9) - (LABEL_RANK.get(b.f.label) ?? 9);
      return d || a.i - b.i;
    })
    .map((x) => x.f);
}

export function buildFinding(flag: ReviewFlag, n: number): FindingVM {
  const left = shortValue(flag.extracted_value);
  const right = shortValue(flag.expected_value);
  const heuristic = isHeuristic(flag);
  return {
    n,
    flag,
    why: whyText(flag),
    limitation: limitationText(flag),
    heuristic,
    aiReader: flag.rule_id === "AI-READER-TEXT",
    values:
      left !== null && right !== null && !heuristic
        ? { left, leftSource: flag.extracted_source?.doc_label ?? "", right, rightSource: flag.expected_source?.label ?? "", unit: flag.value_unit }
        : null,
  };
}

const RANK: Record<LadderState, number> = { disagrees: 4, check: 3, waiting: 2, agrees: 1, na: 0 };
export const worst = (states: LadderState[]): LadderState => states.reduce<LadderState>((a, b) => (RANK[b] > RANK[a] ? b : a), "na");

function outcomeState(label: VerificationLabel): LadderState {
  switch (label) {
    case "verified":
      return "agrees";
    case "mismatch_detected":
    case "expired":
      return "disagrees";
    case "manual_review_required":
      return "check";
    default:
      return "waiting";
  }
}

function signatureState(sig: ReviewDocument["issuer_sig"]): LadderState {
  if (!sig) return "na";
  switch (sig.state) {
    case "verified":
      return "agrees";
    case "chain_broken":
    case "edited_after_signing":
    case "absent_required":
      return "disagrees";
    case "image_only":
    case "present":
      return "check";
    default:
      return "na";
  }
}

export function ladderRow(doc: ReviewDocument, flags: readonly ReviewFlag[]): LadderRow {
  const own = flags.filter((f) => f.doc_id === doc.doc_id);
  const readOk = doc.read.status !== "blocked" && doc.read.reason_code === null;
  const comparisons = own.filter((f) => !isHeuristic(f));
  let portal: LadderState;
  if (comparisons.some((f) => f.label === "mismatch_detected" || f.label === "expired")) portal = "disagrees";
  else if (own.length > 0) portal = "check";
  else portal = doc.label === "verified" ? "agrees" : "na";
  const sources = doc.checks.filter((c) => c.source);
  const first = own[0];
  return {
    docId: doc.doc_id,
    title: doc.title,
    label: doc.label,
    cells: {
      declared: "agrees",
      read: readOk ? "agrees" : "check",
      portal,
      issuer: sources.length === 0 ? "na" : worst(sources.map((c) => outcomeState(c.outcome))),
      signature: worst([signatureState(doc.issuer_sig), signatureState(doc.uploader_sig)]),
    },
    verdictText: first ? whyText(first) : null,
  };
}

export function buildCaseView(review: Review, summary?: string[]): CaseView {
  const ordered = orderFlags(review.flags);
  const findings = ordered.map((f, i) => buildFinding(f, i + 1));
  const disagreeCount = findings.filter((f) => !f.heuristic && (f.flag.label === "mismatch_detected" || f.flag.label === "expired")).length;
  return {
    findings,
    ladder: review.documents.map((d) => ladderRow(d, ordered)),
    disagreeCount,
    lookCount: findings.length - disagreeCount,
    lead: (summary ?? whySummary(review))[0] ?? findings[0]?.why ?? null,
  };
}
