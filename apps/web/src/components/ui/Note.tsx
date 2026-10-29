// Note: the advisory line under a page title. Tinted, fully bordered, icon plus text (no side stripe).
import type { ReactNode } from "react";
import diff from "@/components/diff/DiffView.module.css";
import { Icon } from "@/components/ui/Icon";

export function Note({ children }: { children: ReactNode }) {
  return (
    <p className={diff.advisory}>
      <Icon name="info-circle" size={16} />
      <span>{children}</span>
    </p>
  );
}
