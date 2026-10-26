// Case data for case pages. React cache() lets a segment layout and its page share one Workbench
// API call per request: the layout awaits it before loading.tsx streams, so an unknown case is a
// real HTTP 404 and an out-of-scope case a real 403.
import type { AffidavitDiff, CaseVerification } from "@satya/shared-types";
import { notFound } from "next/navigation";
import { cache } from "react";
import { apiGet } from "./api";

const CASE_ID = /^cas_[0-9A-HJKMNP-TV-Z]{26}$/;

export const affidavitDiff = cache(async (caseId: string, callbackPath: string): Promise<AffidavitDiff> => {
  if (!CASE_ID.test(caseId)) notFound();
  return apiGet<AffidavitDiff>(`/v1/cases/${caseId}/affidavit-diff`, callbackPath);
});

export const caseVerification = cache(async (caseId: string, callbackPath: string): Promise<CaseVerification> => {
  if (!CASE_ID.test(caseId)) notFound();
  return apiGet<CaseVerification>(`/v1/cases/${caseId}/verification`, callbackPath);
});
