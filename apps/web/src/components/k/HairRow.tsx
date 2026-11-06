// A table row as a CSS grid line: top hairline, hover tint. `columns` is a grid-template-columns value.
import type { CSSProperties, ReactNode } from "react";
import styles from "./K.module.css";

export function HairRow({ columns, children, role }: { columns: string; children: ReactNode; role?: "row" }) {
  return (
    <div className={styles.hair} style={{ gridTemplateColumns: columns } as CSSProperties} role={role}>
      {children}
    </div>
  );
}
