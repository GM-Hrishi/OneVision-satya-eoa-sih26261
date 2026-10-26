import type { ReactNode } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { currentPath } from "@/lib/page";

export default async function ShellLayout({ children }: { children: ReactNode }) {
  return <AppShell path={await currentPath()}>{children}</AppShell>;
}
