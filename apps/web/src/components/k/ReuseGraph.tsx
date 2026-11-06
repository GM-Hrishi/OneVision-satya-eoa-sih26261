"use client";
// VISUAL 6: reuse graph. Institutions as circles, artifacts (stamp-paper serial, signature image fingerprint) as boxes
// with a badge counting the institutions that share them. Edges come only from the index. The same facts are in the
// text list below the picture. Always carries "What this does not prove". Development view until an index exists.
import { useTranslations } from "next-intl";
import type { CSSProperties } from "react";
import { useMotion } from "@/components/ui/useMotion";
import { REUSE_W, type ReuseGraph as Graph } from "@/lib/api/k-adapters/reuse";
import { staggerDelay } from "@/lib/motion";
import { inertSnippet } from "@/lib/untrusted";
import styles from "./ReuseGraph.module.css";

export function ReuseGraph({ graph }: { graph: Graph }) {
  const t = useTranslations("k.reuse");
  const tp = useTranslations("k.proof");
  const { cls, runKey, replay } = useMotion();
  const byId = new Map(graph.nodes.map((n) => [n.id, n]));
  const total = graph.nodes.length + graph.edges.length;
  return (
    <div>
      <p>
        <button type="button" className="k-btn k-btn-2" onClick={replay} aria-label={tp("replayLabel")}>
          {tp("replay")}
        </button>
      </p>
      <p className="k-label">{t("caption")}</p>
      <div key={runKey}>
        <svg className={styles.svg} viewBox={`0 0 ${REUSE_W} ${graph.height}`} role="group" aria-label={t("caption")}>
          {graph.edges.map((e, i) => {
            const a = byId.get(e.from);
            const b = byId.get(e.to);
            if (!a || !b) return null;
            return (
              <path key={e.id} className={`${styles.edge} ${cls("draw")}`} style={{ "--d": staggerDelay(graph.nodes.length + i, total) } as CSSProperties} d={`M${a.x + 30} ${a.y} L${b.x - 100} ${b.y}`} pathLength={1} />
            );
          })}
          {graph.nodes.map((n, i) => {
            const name = n.type === "institution" ? t("nodeInstitution", { name: n.label }) : t("nodeArtifact", { kind: t(`kind.${n.kind ?? "stamp_serial"}`), label: n.label, count: n.count });
            return (
              <g key={n.id} className={cls("pop")} style={{ "--d": staggerDelay(i, total) } as CSSProperties} role="img" aria-label={name}>
                <title>{name}</title>
                {n.type === "institution" ? (
                  <>
                    <circle className={styles.inst} cx={n.x} cy={n.y} r={30} />
                    <text className={styles.text} x={n.x + 40} y={n.y + 5}>
                      {inertSnippet(n.label, 30)}
                    </text>
                  </>
                ) : (
                  <>
                    <rect className={styles.box} x={n.x - 100} y={n.y - 26} width={230} height={52} />
                    <text className={styles.text} x={n.x - 90} y={n.y - 4}>
                      {inertSnippet(n.label, 24)}
                    </text>
                    <text className={styles.sub} x={n.x - 90} y={n.y + 14}>
                      {t(`kind.${n.kind ?? "stamp_serial"}`)}
                    </text>
                    <circle className={styles.badge} cx={n.x + 130} cy={n.y - 26} r={14} />
                    <text className={styles.badgeText} x={n.x + 130} y={n.y - 21} textAnchor="middle" aria-hidden="true">
                      {n.count}
                    </text>
                  </>
                )}
              </g>
            );
          })}
        </svg>
      </div>
      <ul className={styles.list}>
        {graph.nodes
          .filter((n) => n.type === "artifact")
          .map((n) => (
            <li key={n.id}>
              <strong>{inertSnippet(n.label, 40)}</strong> {t("badge", { count: n.count })}
            </li>
          ))}
      </ul>
      <aside className={styles.note}>
        <strong className="k-label">{tp("limitationLabel")}</strong>
        <p style={{ margin: 0 }}>{t("notProve")}</p>
      </aside>
    </div>
  );
}
