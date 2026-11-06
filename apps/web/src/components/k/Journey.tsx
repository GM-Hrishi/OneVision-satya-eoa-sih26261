"use client";
// VISUAL 2: the document journey. One row per document, five steps. Each step shows an icon AND its state
// in words. A step that stops the flow gets a pulse ring and the plain reason. Steps light up left to right,
// rows staggered (total stagger capped); Replay re-keys. Entry numbers are not shown (see adapters/journey.ts).
import { useTranslations } from "next-intl";
import type { CSSProperties } from "react";
import { Icon, type IconName } from "@/components/ui/Icon";
import { StatusLabel } from "@/components/ui/StatusLabel";
import { useMotion } from "@/components/ui/useMotion";
import { JOURNEY_STEPS, type JourneyRow } from "@/lib/api/k-adapters/journey";
import type { LadderState } from "@/lib/api/k-adapters/case";
import { staggerDelay } from "@/lib/motion";
import styles from "./Proof.module.css";

const ICON: Record<LadderState, IconName> = { agrees: "circle-check", disagrees: "circle-x", waiting: "hourglass", check: "user-search", na: "minus" };

export function Journey({ rows }: { rows: JourneyRow[] }) {
  const t = useTranslations("k.proof");
  const ts = useTranslations("k.ladder.state");
  const tv = useTranslations("k.ladder.verdict");
  const { cls, runKey, replay } = useMotion();
  if (rows.length === 0) return <p className={styles.plain}>{t("noJourney")}</p>;
  const total = rows.length * JOURNEY_STEPS.length;
  return (
    <div>
      <div className={styles.bar}>
        <button type="button" className={styles.replay} onClick={replay} aria-label={t("replayLabel")}>
          {t("replay")}
        </button>
      </div>
      <div className={styles.scroll} key={runKey}>
        <table className={styles.table}>
          <caption className="k-label">{t("journeyCaption")}</caption>
          <thead>
            <tr>
              <th scope="col" className="k-label" />
              {JOURNEY_STEPS.map((s) => (
                <th key={s} scope="col" className="k-label">
                  {t(`step.${s}`)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, r) => (
              <tr key={row.docId}>
                <th scope="row">
                  <span className={styles.docTitle}>{row.title}</span>
                  <br />
                  <StatusLabel label={row.label} size="sm" />
                  <p className={styles.verdict}>{row.verdictText ?? tv(row.label, { title: row.title })}</p>
                  {row.stoppedAt ? (
                    <p className={styles.stop}>
                      {t("stopped", { reason: row.stopReasonText ?? (row.stopReasonKey === "source" ? t("stopSource") : t("stopUnreadable")) })}
                    </p>
                  ) : null}
                </th>
                {JOURNEY_STEPS.map((s, c) => {
                  const state = row.steps[s];
                  const d = staggerDelay(r * JOURNEY_STEPS.length + c, total);
                  return (
                    <td key={s}>
                      <span
                        className={`${styles.step} ${cls("pop")}`}
                        style={{ "--d": d } as CSSProperties}
                        data-state={state}
                        aria-label={t("stepCell", { step: t(`step.${s}`), state: ts(state) })}
                      >
                        {row.stoppedAt === s ? <span className={`${styles.ring} ${cls("ping")}`} style={{ "--d": d } as CSSProperties} aria-hidden="true" /> : null}
                        <Icon name={ICON[state]} size={18} />
                        {ts(state)}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
