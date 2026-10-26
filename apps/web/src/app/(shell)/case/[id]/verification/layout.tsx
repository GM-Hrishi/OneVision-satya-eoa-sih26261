import type { ReactNode } from "react";
import { affidavitDiff, caseVerification } from "@/lib/cases";

// Fetch before the page streams so 404/403 keep their status codes (see src/lib/cases.ts).
export default async function VerificationLayout({ children, params }: { children: ReactNode; params: Promise<{ id: string }> }) {
  const { id } = await params;
  const back = `/case/${id}/verification`;
  await Promise.all([caseVerification(id, back), affidavitDiff(id, back)]);
  return children;
}
