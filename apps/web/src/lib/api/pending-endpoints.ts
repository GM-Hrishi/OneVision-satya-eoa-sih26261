// Endpoints and fields that exist on the backend branch feat/logic-rival-parity (draft PR #15) and
// are NOT on main yet. Until that PR merges they answer 404 here, and every consumer shows the honest
// "not available" state (or its documented fallback). Shapes: docs/API-NOTES.md on that branch.
// Never call these without handling 404. After the merge: regenerate shared types, delete the
// accessors in k-adapters, run the e2e and smoke tests (docs/ui-style-k/MERGE-NOTES.md).

/** NOT ON MAIN UNTIL PR #15 MERGES */
export const AUDIT_VERIFY = "/v1/audit/verify";
/** NOT ON MAIN UNTIL PR #15 MERGES */
export const replayCheck = (caseId: string) => `/v1/cases/${caseId}/replay-check`;
/** NOT ON MAIN UNTIL PR #15 MERGES. Optional query: from_seq, to_seq. */
export const runDiff = (caseId: string) => `/v1/cases/${caseId}/run-diff`;
/** NOT ON MAIN UNTIL PR #15 MERGES */
export const ruleDetail = (ruleId: string) => `/v1/rules/${encodeURIComponent(ruleId)}`;

/**
 * Optional fields on existing responses, also NOT ON MAIN UNTIL PR #15 MERGES:
 * flag.limitation {key,text}|null, flag.why_detail {key,params,text}, flag.check_kind "heuristic",
 * review and queue row why_summary string[<=3], affidavit-diff summary {...}, expiry check coverage {...},
 * GET /v1/cases/{id}/replay as_of, digest_original, digest_replayed.
 */
export const PENDING_FIELDS = ["limitation", "why_detail", "check_kind", "why_summary", "summary", "coverage", "digest_original", "digest_replayed"] as const;
