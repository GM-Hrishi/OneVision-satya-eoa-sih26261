// The six verification labels, most severe first (Portal spec §2.6.3). Same order as the generated
// LABEL_PRECEDENCE in @satya/shared-types (pinned by test/labels.test.ts); kept here as a type-only
// import because the workbench bundles only types from the shared package.
import type { VerificationLabel } from "@satya/shared-types";

export const LABEL_ORDER: readonly VerificationLabel[] = [
  "mismatch_detected",
  "expired",
  "manual_review_required",
  "source_unavailable",
  "verification_pending",
  "verified",
];
