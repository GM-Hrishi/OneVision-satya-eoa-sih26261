import type { ReactNode } from "react";
import styles from "./Page.module.css";

export function PageHeader({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className={styles.header}>
      <h1>{title}</h1>
      {children}
    </div>
  );
}
