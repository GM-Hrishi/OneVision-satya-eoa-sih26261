// Slice D (demo flow) data: queue, case review, alerts and audit from the Workbench API (server only).
import { notFound } from "next/navigation";
import { cache } from "react";
import { apiGet, apiGetQuiet } from "./api";
import type { Audit, Overview, AlertItem, QueueRow, Review, Band, SortDir, SortKey } from "./demo-types";

export * from "./demo-types";

const CASE_ID = /^cas_[0-9A-HJKMNP-TV-Z]{26}$/;

export interface QueueResponse {
  items: QueueRow[];
  totals: { submitted: number; by_band: Record<Band, number>; sources_unavailable: number };
  sort: { key: SortKey; dir: SortDir; default: boolean; within: "risk_band" };
}

/** The queue, ordered by the API: risk band groups first, `sort` inside each group. */
export const queue = (path: string, sort?: { key: SortKey; dir: SortDir }) => {
  const query = sort ? `?sort=${sort.key}&dir=${sort.dir}` : "";
  return apiGet<QueueResponse>(`/v1/cases${query}`, path);
};

export const caseReview = cache(async (caseId: string, callbackPath: string): Promise<Review> => {
  if (!CASE_ID.test(caseId)) notFound();
  return apiGet<Review>(`/v1/cases/${caseId}/review`, callbackPath);
});

export const overview = (path: string, ay: string) => apiGet<Overview>(`/v1/overview?ay=${encodeURIComponent(ay)}`, path);

export const alerts = (path: string) => apiGet<{ items: AlertItem[] }>("/v1/alerts", path);
export const alertsQuiet = () => apiGetQuiet<{ items: AlertItem[] }>("/v1/alerts");

export const audit = (path: string, caseId?: string) =>
  apiGet<Audit>(caseId && CASE_ID.test(caseId) ? `/v1/audit?case_id=${caseId}` : "/v1/audit", path);
