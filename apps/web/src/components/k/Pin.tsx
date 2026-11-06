// Numbered pin linking a finding, its place on the document and the decision (emphasis rule 5).
// Decorative: the same information is always in the text next to it, so the pin is aria-hidden.
import styles from "./K.module.css";

export type PinTone = "red" | "ink" | "accent";

/** Pin 1 is red, pin 2 ink, pin 3 accent; later pins repeat ink. */
export function pinTone(n: number): PinTone {
  return n === 1 ? "red" : n === 3 ? "accent" : "ink";
}

export function Pin({ n, tone }: { n: number; tone?: PinTone }) {
  return (
    <span className={styles.pin} data-tone={tone ?? pinTone(n)} aria-hidden="true">
      {n}
    </span>
  );
}
