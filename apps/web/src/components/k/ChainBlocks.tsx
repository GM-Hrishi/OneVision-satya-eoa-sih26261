// Linked entry blocks: the latest four ledger entries in chain order, each with its number, what it was,
// a short fingerprint and the fingerprint of the entry it follows (when that entry is in this view).
import { getTranslations } from "next-intl/server";
import type { AuditEntry } from "@/lib/demo-types";
import styles from "./Audit.module.css";

const short = (hash: string) => hash.slice(0, 10);

export async function ChainBlocks({ entries, eventLabel }: { entries: AuditEntry[]; eventLabel: (kind: string) => string }) {
  const t = await getTranslations("k.audit");
  if (entries.length === 0) return <p>{t("blocksNone")}</p>;
  const bySeq = new Map(entries.map((e) => [e.seq, e]));
  // `entries` arrive newest first; show the latest four in chain order (oldest of the four first).
  const last = entries.slice(0, 4).reverse();
  return (
    <ol className={styles.blocks} aria-label={t("blocksHeading")}>
      {last.map((e, i) => {
        const prev = bySeq.get(e.seq - 1);
        return (
          <li key={e.seq} className={styles.block}>
            {i > 0 ? <span className={styles.connector} aria-hidden="true" /> : null}
            <div className={styles.card}>
              <span className={styles.cardNo}>{t("entry", { no: e.seq })}</span>
              <span>{eventLabel(e.event_type)}</span>
              <span className={styles.cardHash}>{t("fingerprint", { hash: short(e.hash) })}</span>
              <span className={styles.cardHash}>{prev ? t("follows", { hash: short(prev.hash) }) : t("firstEntry")}</span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
