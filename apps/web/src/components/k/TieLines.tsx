"use client";
// VISUAL 3: tie lines. Sworn copy on the left (paper), portal form on the right, a fixed 200px SVG between them
// with one line per declaration. Matches are thin grey; a difference is a thick accent line with a chip that
// states the difference in words. Rows have a fixed height so the lines align. Rows rise in, lines draw left to
// right, the differing rows flash last; Replay re-keys. Below 1024px the view falls back to the Table.
// Text is the API's own and is rendered as plain text, cut to two lines (the Table view shows it in full).
import { useTranslations } from "next-intl";
import { useState, type CSSProperties } from "react";
import { useMotion } from "@/components/ui/useMotion";
import type { TieRow } from "@/lib/api/k-adapters/affidavit";
import { staggerDelay } from "@/lib/motion";
import { inertSnippet } from "@/lib/untrusted";
import styles from "./Tie.module.css";

const ROW_H = 56;

export function TieLines({ rows, compared, onUseTable }: { rows: TieRow[]; compared: boolean; onUseTable: () => void }) {
  const t = useTranslations("k.affidavit");
  const { cls, runKey, replay } = useMotion();
  const [all, setAll] = useState(false);
  if (!compared) return <p role="status">{t("tieNotCompared")}</p>;
  const differing = rows.filter((r) => r.op !== "equal");
  const shown = all ? rows : differing;
  if (shown.length === 0) {
    return (
      <div>
        <p role="status">{t("tieNone")}</p>
        {rows.length > 0 ? (
          <button type="button" className={styles.btn} onClick={() => setAll(true)}>
            {t("tieShowAll")}
          </button>
        ) : null}
      </div>
    );
  }
  const lastFlash = shown.length;
  return (
    <div>
      <div className={styles.fallback}>
        <p>{t("tieNotCompared")}</p>
        <button type="button" className={styles.btn} onClick={onUseTable}>
          {t("viewTable")}
        </button>
      </div>
      <div className={styles.tieOnly}>
        <div className={styles.bar}>
          <button type="button" className={styles.btn} onClick={replay}>
            {t("replay")}
          </button>
          <button type="button" className={styles.btn} onClick={() => setAll((v) => !v)}>
            {all ? t("tieShowChanged") : t("tieShowAll")}
          </button>
        </div>
        <p className={styles.caption}>{t("tieCaption")}</p>
        <div className={styles.heads}>
          <span className="k-label">{t("tieLeft")}</span>
          <span />
          <span className="k-label">{t("tieRight")}</span>
        </div>
        <div className={styles.grid} key={runKey}>
          <ol className={`${styles.col} ${styles.paper}`} aria-label={t("tieLeft")}>
            {shown.map((r, i) => (
              <li key={r.key} className={`${styles.cell} ${cls("rise")}`} style={{ "--d": staggerDelay(i, shown.length, 0.08) } as CSSProperties} data-op={r.op}>
                <span className={styles.no}>{t("tieNo", { no: r.no })}</span>
                {r.sworn ? <span className={styles.text}>{inertSnippet(r.sworn, 140)}</span> : <span className={styles.empty}>{t("tieMissing")}</span>}
              </li>
            ))}
          </ol>
          <div className={styles.mid} aria-hidden="true">
            <svg className={styles.svg} width={200} height={shown.length * ROW_H} viewBox={`0 0 200 ${shown.length * ROW_H}`}>
              {shown.map((r, i) => {
                const y = i * ROW_H + ROW_H / 2;
                const diff = r.op !== "equal";
                return (
                  <line
                    key={r.key}
                    className={`${diff ? styles.lineDiff : styles.lineMatch} ${cls("draw")}`}
                    style={{ "--d": staggerDelay(i, shown.length, 0.08) } as CSSProperties}
                    x1={0}
                    x2={200}
                    y1={y}
                    y2={y}
                    pathLength={1}
                  />
                );
              })}
            </svg>
            {shown.map((r, i) =>
              r.op !== "equal" ? (
                <span key={r.key} className={`${styles.chip} ${cls("pop")}`} style={{ top: i * ROW_H + ROW_H / 2 - 12, "--d": staggerDelay(lastFlash, lastFlash + 1, 0.08) } as CSSProperties}>
                  {t(`chip.${r.op}`)}
                </span>
              ) : null,
            )}
          </div>
          <ol className={`${styles.col} ${styles.paper}`} aria-label={t("tieRight")}>
            {shown.map((r, i) => (
              <li
                key={r.key}
                className={`${styles.cell} ${cls("rise")} ${r.op !== "equal" ? cls("flash") : ""}`}
                style={{ "--d": r.op !== "equal" ? `${(0.8 + i * 0.05).toFixed(2)}s` : staggerDelay(i, shown.length, 0.08) } as CSSProperties}
                data-op={r.op}
              >
                <span className={styles.no}>{t("tieNo", { no: r.no })}</span>
                {r.portal ? <span className={styles.text}>{inertSnippet(r.portal, 140)}</span> : <span className={styles.empty}>{t("tieAdded")}</span>}
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}
