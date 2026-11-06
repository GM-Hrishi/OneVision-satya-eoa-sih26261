// VISUAL 2: the document journey. One row per document, five steps. Every state comes from the review payload
// (read summary, findings, source checks, signature checks). Audit entry numbers are NOT shown: the ledger
// events found on main (document.read, check.run, ...) are written per run, not per step, so they cannot be
// attached to a single step honestly (see docs/progress/ui-style-k.md, T0 note 9).
import type { Review, ReviewDocument } from "@/lib/demo-types";
import { buildCaseView, type LadderState } from "./case";

export const JOURNEY_STEPS = ["template", "fields", "rules", "issuer", "signature"] as const;
export type JourneyStep = (typeof JOURNEY_STEPS)[number];

export interface JourneyRow {
  docId: string;
  title: string;
  label: ReviewDocument["label"];
  steps: Record<JourneyStep, LadderState>;
  /** The first step that stops the flow, or null. */
  stoppedAt: JourneyStep | null;
  /** Plain reason for the stop: the API's fixed read sentence, else a key the view translates. */
  stopReasonText: string | null;
  stopReasonKey: "unreadable" | "source" | null;
  verdictText: string | null;
}

export function buildJourney(review: Review): JourneyRow[] {
  const view = buildCaseView(review);
  return view.ladder.map((row) => {
    const doc = review.documents.find((d) => d.doc_id === row.docId);
    const c = row.cells;
    const readStops = c.read === "check";
    const steps: Record<JourneyStep, LadderState> = {
      template: doc && doc.read.status !== "blocked" ? "agrees" : "check",
      fields: c.read,
      rules: readStops ? "waiting" : c.portal === "na" ? "agrees" : c.portal,
      issuer: readStops && c.issuer === "na" ? "na" : c.issuer,
      signature: c.signature,
    };
    let stoppedAt: JourneyStep | null = null;
    let stopReasonKey: JourneyRow["stopReasonKey"] = null;
    if (steps.template === "check") {
      stoppedAt = "template";
      stopReasonKey = "unreadable";
    } else if (readStops) {
      stoppedAt = "fields";
      stopReasonKey = "unreadable";
    } else if (steps.issuer === "waiting") {
      stoppedAt = "issuer";
      stopReasonKey = "source";
    }
    return {
      docId: row.docId,
      title: row.title,
      label: row.label,
      steps,
      stoppedAt,
      stopReasonText: stoppedAt === "template" || stoppedAt === "fields" ? (doc?.read.why ?? null) : null,
      stopReasonKey,
      verdictText: row.verdictText,
    };
  });
}
