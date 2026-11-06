// A critical number, huge and condensed (emphasis rule 1). Colour only for mismatch (red) or the accent.
import type { ReactNode } from "react";
import styles from "./K.module.css";

export interface NumeralProps {
  value: ReactNode;
  /** One-line caption in the small-caps label style. */
  caption?: ReactNode;
  tone?: "accent" | "red" | "ink";
}

export function Numeral({ value, caption, tone = "accent" }: NumeralProps) {
  return (
    <div className={styles.numeral}>
      <span className="k-big" data-tone={tone}>
        {value}
      </span>
      {caption ? <span className={`k-label ${styles.caption}`}>{caption}</span> : null}
    </div>
  );
}
