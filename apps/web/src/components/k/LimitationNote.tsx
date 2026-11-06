"use client";
// "What this does not prove" (emphasis rule 4). Shown ONLY when the API supplies limitation text for the
// finding: no text, no note (never a key, never a client-side guess). The text is the API's own, already in
// the chosen language; it is rendered as plain text.
import { useTranslations } from "next-intl";
import styles from "./K.module.css";

export function LimitationNote({ text }: { text: string | null | undefined }) {
  const t = useTranslations("k");
  if (!text?.trim()) return null;
  return (
    <aside className={styles.note}>
      <strong className={`k-label ${styles.noteTitle}`}>{t("limitation.title")}</strong>
      <p className={styles.noteText}>{text}</p>
    </aside>
  );
}
