import type { ReactNode } from "react";
import { affidavitDiff } from "@/lib/cases";

// Fetch before the page streams so 404/403 keep their status codes (see src/lib/cases.ts).
export default async function AffidavitLayout({ children, params }: { children: ReactNode; params: Promise<{ id: string }> }) {
  const { id } = await params;
  await affidavitDiff(id, `/case/${id}/affidavit`);
  return children;
}
