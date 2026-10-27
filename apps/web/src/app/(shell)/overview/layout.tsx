// Authorisation runs here, before loading.tsx starts streaming, so a missing session gets a real
// 307 to sign-in and a wrong role a real 403 (the page repeats the check).
import type { ReactNode } from "react";
import { currentPath } from "@/lib/page";
import { requireRole } from "@/lib/session";

export default async function OverviewLayout({ children }: { children: ReactNode }) {
  await requireRole("RB", await currentPath());
  return children;
}
