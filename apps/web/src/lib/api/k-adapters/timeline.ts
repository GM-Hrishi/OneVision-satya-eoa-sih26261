// VISUAL 4: queue timeline. One point per case on a days-waiting axis. Pure and tested.
// Position is days waiting only. It never implies decision order, and the page says so in a caption.
import type { Band, QueueRow } from "@/lib/demo-types";
import { waitingDays } from "./queue";

export interface TimelinePoint {
  caseId: string;
  applicationId: string;
  /** Last four characters of the application ID, shown beside the dot. */
  tail: string;
  band: Band;
  days: number;
  /** 0 for the first dot on a given day, 1 for the next, and so on (dots with the same day are stacked). */
  stack: number;
  longest: boolean;
}

export interface Timeline {
  points: TimelinePoint[];
  maxDays: number;
  maxStack: number;
}

export function buildTimeline(rows: readonly QueueRow[], asOf: string): Timeline {
  const dated = rows
    .map((r) => ({ r, days: waitingDays(r.submitted_at, asOf) }))
    .filter((x): x is { r: QueueRow; days: number } => x.days !== null);
  const maxDays = dated.reduce((m, x) => Math.max(m, x.days), 0);
  const seen = new Map<number, number>();
  const points = dated.map(({ r, days }) => {
    const stack = seen.get(days) ?? 0;
    seen.set(days, stack + 1);
    return {
      caseId: r.case_id,
      applicationId: r.application_id,
      tail: r.application_id.slice(-4),
      band: r.risk_band,
      days,
      stack,
      longest: false,
    };
  });
  // "Waited longest" marks every dot on the maximum day, but only when somebody waited at all.
  for (const p of points) p.longest = maxDays > 0 && p.days === maxDays;
  return { points, maxDays, maxStack: Math.max(0, ...points.map((p) => p.stack)) };
}
