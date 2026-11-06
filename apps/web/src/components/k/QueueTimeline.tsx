"use client";
// VISUAL 4: the queue timeline. One SVG axis in days waiting; one circle per case with its band letter inside
// (never colour alone), stacked when days coincide, the last four digits of the application ID beside it, an
// accessible name and keyboard focus per dot. Position is days waiting only; the caption says it never implies
// decision order. The "Waited longest" annotation sits on the maximum.
import { useTranslations } from "next-intl";
import Link from "next/link";
import type { Timeline } from "@/lib/api/k-adapters/timeline";
import styles from "./QueueTimeline.module.css";

const W = 900;
const LEFT = 48;
const RIGHT = 70;
const R = 16;
const STEP = 38;

export function QueueTimeline({ timeline }: { timeline: Timeline }) {
  const t = useTranslations("k.queue");
  const tb = useTranslations("demo.band");
  if (timeline.points.length === 0) return <p>{t("timelineEmpty")}</p>;
  const span = Math.max(timeline.maxDays, 1);
  const x = (days: number) => LEFT + ((W - LEFT - RIGHT) * days) / span;
  const base = 70 + timeline.maxStack * STEP;
  const H = base + 54;
  const ticks = Array.from({ length: span + 1 }, (_, d) => d);
  const every = span > 14 ? Math.ceil(span / 14) : 1;
  return (
    <div>
      <svg className={styles.svg} viewBox={`0 0 ${W} ${H}`} role="group" aria-label={t("timelineCaption")}>
        <line className={styles.axis} x1={LEFT - 12} x2={W - RIGHT + 12} y1={base} y2={base} />
        {ticks
          .filter((d) => d % every === 0)
          .map((d) => (
            <g key={d} aria-hidden="true">
              <line className={styles.tick} x1={x(d)} x2={x(d)} y1={base - 4} y2={base + 6} />
              <text className={styles.tickText} x={x(d)} y={base + 22} textAnchor="middle">
                {t("dayTick", { days: d })}
              </text>
            </g>
          ))}
        <text className={styles.axisText} x={W - RIGHT + 12} y={base + 44} textAnchor="end" aria-hidden="true">
          {t("axis")}
        </text>
        {timeline.points.map((p) => {
          const cx = x(p.days);
          const cy = base - 30 - p.stack * STEP;
          const band = tb(p.band);
          const name = t("dotLabel", { id: p.applicationId, band, days: p.days });
          return (
            <g key={p.caseId} className={styles.dot} data-band={p.band}>
              <Link href={`/case/${p.caseId}`} className={styles.link} aria-label={name}>
                <title>{name}</title>
                <circle className={styles.circle} cx={cx} cy={cy} r={R} />
                <text className={styles.letter} x={cx} y={cy + 5} textAnchor="middle" aria-hidden="true">
                  {Array.from(band)[0]?.toUpperCase()}
                </text>
                <text className={styles.tail} x={cx + R + 5} y={cy + 4} aria-hidden="true">
                  {p.tail}
                </text>
              </Link>
              {p.longest && p.stack === 0 ? (
                <text className={styles.longest} x={cx} y={cy - R - 8} textAnchor="middle">
                  {t("longest")}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
      <p className={styles.caption}>
        {t("timelineCaption")} {t("timelineNote")}
      </p>
    </div>
  );
}
