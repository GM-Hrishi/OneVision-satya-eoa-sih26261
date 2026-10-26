// Case pages are for Regulation Bureau officials (UI spec §2.2). Authorisation runs here, before
// loading.tsx streams, so a missing session gets a real redirect and a wrong role a real 403. The
// gateway checks role and region again on every API call.
import type { ReactNode } from "react";
import { currentPath } from "@/lib/page";
import { requireRole } from "@/lib/session";

export default async function CaseLayout({ children }: { children: ReactNode }) {
  await requireRole("RB", await currentPath());
  return children;
}
