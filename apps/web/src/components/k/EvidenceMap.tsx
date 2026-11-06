"use client";
// VISUAL 1: the evidence map. SVG, responsive via viewBox. Lines exist only where the builder found a source
// (a finding or a source check). Document nodes are focusable links; everything the picture shows is also in
// the text list beside it, so the SVG is a visual aid, not the only carrier. Motion: nodes pop in sequence,
// solid lines draw, red pins ping (3 times). Dashed and dotted lines pop in instead, because a dash pattern
// cannot also be the draw mask. Replay re-keys the picture.
import { useTranslations } from "next-intl";
import Link from "next/link";
import type { CSSProperties } from "react";
import { useMotion } from "@/components/ui/useMotion";
import type { EdgeState, EvidenceGraph, GraphEdge, GraphNode } from "@/lib/api/k-adapters/graph";
import { staggerDelay } from "@/lib/motion";
import { inertSnippet } from "@/lib/untrusted";
import { Pin } from "./Pin";
import styles from "./Proof.module.css";

export interface MapFinding {
  n: number;
  rule: string;
  why: string;
}

const NODE_W = 210;
const NODE_H = 58;
const STATES: EdgeState[] = ["agrees", "disagrees", "waiting", "check"];
const delay = (s: string) => ({ "--d": s }) as CSSProperties;

function endpoints(a: GraphNode, b: GraphNode) {
  return { x1: a.x + NODE_W / 2, y1: a.y, x2: b.x - NODE_W / 2, y2: b.y };
}

export function EvidenceMap({ graph, findings, caseId }: { graph: EvidenceGraph; findings: MapFinding[]; caseId: string }) {
  const t = useTranslations("k.proof");
  const ts = useTranslations("k.ladder.state");
  const { cls, runKey, replay } = useMotion();
  const byId = new Map(graph.nodes.map((n) => [n.id, n]));
  const titleOf = (n: GraphNode | undefined) => (n?.kind === "portal" ? t("mapPortal") : (n?.title ?? ""));
  if (graph.edges.length === 0) {
    return <p className={styles.plain}>{t("noEdges")}</p>;
  }
  const total = graph.nodes.length + graph.edges.length;
  return (
    <div>
      <div className={styles.bar}>
        <button type="button" className={styles.replay} onClick={replay} aria-label={t("replayLabel")}>
          {t("replay")}
        </button>
      </div>
      <div className={styles.mapLayout}>
        <div key={runKey}>
          <svg className={styles.svg} viewBox={`0 0 ${graph.width} ${graph.height}`} role="group" aria-label={t("mapCaption")}>
            {graph.edges.map((e: GraphEdge, i) => {
              const a = byId.get(e.from);
              const b = byId.get(e.to);
              if (!a || !b) return null;
              const p = endpoints(a, b);
              const solid = e.state === "agrees" || e.state === "disagrees";
              const d = staggerDelay(graph.nodes.length + i, total);
              const mx = (p.x1 + p.x2) / 2;
              const my = (p.y1 + p.y2) / 2;
              return (
                <g key={e.id}>
                  <path
                    className={`${styles.edge} ${solid ? cls("draw") : cls("pop")}`}
                    style={delay(d)}
                    data-state={e.state}
                    d={`M${p.x1} ${p.y1} L${p.x2} ${p.y2}`}
                    pathLength={1}
                  />
                  {e.pin !== null ? (
                    <g aria-hidden="true">
                      <circle className={`${styles.pinRing} ${cls("ping")}`} style={delay(d)} cx={mx} cy={my} r={14} />
                      <circle className={styles.pinCircle} cx={mx} cy={my} r={14} />
                      <text className={styles.pinText} x={mx} y={my + 5} textAnchor="middle">
                        {e.pin}
                      </text>
                    </g>
                  ) : null}
                </g>
              );
            })}
            {graph.nodes.map((n, i) => {
              const label = inertSnippet(titleOf(n), 26);
              const body = (
                <>
                  <title>{titleOf(n)}</title>
                  <rect className={styles.nodeRect} x={n.x - NODE_W / 2} y={n.y - NODE_H / 2} width={NODE_W} height={NODE_H} />
                  <text className={styles.nodeText} x={n.x} y={n.y + 5} textAnchor="middle">
                    {label}
                  </text>
                </>
              );
              return (
                <g key={n.id} className={`${styles.node} ${cls("pop")}`} style={delay(staggerDelay(i, total))} data-kind={n.kind}>
                  {n.docId ? (
                    <Link href={`/case/${caseId}/documents/${n.docId}`} className={styles.nodeLink} aria-label={t("openDocument", { title: titleOf(n) })}>
                      {body}
                    </Link>
                  ) : (
                    body
                  )}
                </g>
              );
            })}
          </svg>
          <ul className={styles.legend} aria-label={t("legendTitle")}>
            {STATES.map((s) => (
              <li key={s}>
                <span className={styles.sample} data-state={s} aria-hidden="true" />
                {t(`line.${s}`)}
              </li>
            ))}
          </ul>
        </div>
        <div className={styles.panel}>
          <h3>{t("findingsHeading")}</h3>
          <ul className={styles.list}>
            {findings.map((f) => (
              <li key={f.n}>
                <Pin n={f.n} />
                <span>
                  <strong>{f.rule}</strong>
                  <br />
                  {f.why}
                </span>
              </li>
            ))}
          </ul>
          <h3>{t("relations")}</h3>
          <ul className={styles.list}>
            {graph.edges.map((e) => (
              <li key={e.id}>
                <span>
                  {e.findings.length > 0
                    ? t("relationFinding", { from: titleOf(byId.get(e.from)), to: titleOf(byId.get(e.to)), state: ts(e.state), n: e.findings.join(", ") })
                    : t("relation", { from: titleOf(byId.get(e.from)), to: titleOf(byId.get(e.to)), state: ts(e.state) })}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
