// Slice D (demo flow) data: queue, case review, alerts and audit from the Workbench API (server only).
import { notFound } from "next/navigation";
import { cache } from "react";
import { apiGet } from "./api";
import type { Audit, AlertItem, QueueRow, Review, Band } from "./demo-types";

export * from "./demo-types";

const CASE_ID = /^cas_[0-9A-HJKMNP-TV-Z]{26}$/;

export const queue = (path: string) =>
  apiGet<{ items: QueueRow[]; totals: { submitted: number; by_band: Record<Band, number>; sources_unavailable: number } }>("/v1/cases", path);

export const caseReview = cache(async (caseId: string, callbackPath: string): Promise<Review> => {
  if (!CASE_ID.test(caseId)) notFound();
  return apiGet<Review>(`/v1/cases/${caseId}/review`, callbackPath);
});

export const alerts = (path: string) => apiGet<{ items: AlertItem[] }>("/v1/alerts", path);

export const audit = (path: string, caseId?: string) =>
  apiGet<Audit>(caseId && CASE_ID.test(caseId) ? `/v1/audit?case_id=${caseId}` : "/v1/audit", path);
