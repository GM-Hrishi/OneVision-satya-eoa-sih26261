// SortIndicator: two stacked triangles (8px base, 5px high each). Idle: both grey. Active: the
// current direction in the active colour, the other at 35% opacity. Decorative; the column header
// carries aria-sort and a polite announcement says the change in words.
import styles from "./SortIndicator.module.css";

export type SortDirection = "ascending" | "descending" | undefined;

export function SortIndicator({ direction }: { direction: SortDirection }) {
  return (
    <svg className={styles.sort} width="8" height="12" viewBox="0 0 8 12" aria-hidden="true" focusable="false" data-direction={direction ?? "none"}>
      <path className={styles.up} d="M4 0 L8 5 H0 Z" />
      <path className={styles.down} d="M4 12 L8 7 H0 Z" />
    </svg>
  );
}
