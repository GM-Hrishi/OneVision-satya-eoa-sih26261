// VISUAL 1: the evidence map. buildEvidenceGraph is pure and never creates an edge without a source: every
// edge carries `source` (a flag id or a source-check reference) and a list of the findings behind it.
// Nodes: the portal form, every document, and each issuer source that answered. Edges: a flag that relates a
// document to the portal form, and a source check that relates a document to its issuer.
import type { VerificationLabel } from "@satya/shared-types";
import type { Review } from "@/lib/demo-types";
import { buildCaseView, worst } from "./case";

export type EdgeState = "agrees" | "disagrees" | "waiting" | "check";
export type NodeKind = "portal" | "document" | "issuer";

export interface GraphNode {
  id: string;
  kind: NodeKind;
  title: string;
  docId: string | null;
  x: number;
  y: number;
}

export interface GraphEdge {
  id: string;
  from: string;
  to: string;
  state: EdgeState;
  /** Where the edge comes from: "flag:<flag id>" or "check:<doc id>:<adapter id>:<kind>". Never empty. */
  source: string;
  /** Finding numbers (pins) behind the edge, lowest first. Empty for a source-check edge. */
  findings: number[];
  /** The pin shown on the edge: the lowest finding number when the edge disagrees. */
  pin: number | null;
}

export interface EvidenceGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  width: number;
  height: number;
}

export const GRAPH_W = 900;
export const GRAPH_H = 540;
const PORTAL_ID = "portal";
const COLX = { portal: 130, document: 450, issuer: 770 } as const;

const outcomeState = (label: VerificationLabel): EdgeState =>
  label === "verified" ? "agrees" : label === "mismatch_detected" || label === "expired" ? "disagrees" : label === "manual_review_required" ? "check" : "waiting";

function column(ids: string[]): number[] {
  const top = 80;
  const bottom = GRAPH_H - 80;
  if (ids.length <= 1) return ids.map(() => GRAPH_H / 2);
  const step = (bottom - top) / (ids.length - 1);
  return ids.map((_, i) => Math.round(top + i * step));
}

export function buildEvidenceGraph(review: Review): EvidenceGraph {
  const view = buildCaseView(review);
  const docs = review.documents;
  const sources = new Map<string, string>();
  for (const d of docs) for (const c of d.checks) if (c.source) sources.set(c.source.adapter_id, c.source.name);

  const docYs = column(docs.map((d) => d.doc_id));
  const srcIds = [...sources.keys()];
  const srcYs = column(srcIds);
  const nodes: GraphNode[] = [];
  if (docs.length > 0) nodes.push({ id: PORTAL_ID, kind: "portal", title: "", docId: null, x: COLX.portal, y: GRAPH_H / 2 });
  docs.forEach((d, i) => nodes.push({ id: d.doc_id, kind: "document", title: d.title, docId: d.doc_id, x: COLX.document, y: docYs[i] ?? GRAPH_H / 2 }));
  srcIds.forEach((id, i) => nodes.push({ id: `src:${id}`, kind: "issuer", title: sources.get(id) ?? id, docId: null, x: COLX.issuer, y: srcYs[i] ?? GRAPH_H / 2 }));

  const edges = new Map<string, GraphEdge>();
  const docIds = new Set(docs.map((d) => d.doc_id));
  for (const f of view.findings) {
    const docId = f.flag.doc_id;
    if (!docId || !docIds.has(docId)) continue; // a finding with no document relates nothing we can draw
    const state: EdgeState = f.heuristic ? "check" : f.flag.label === "mismatch_detected" || f.flag.label === "expired" ? "disagrees" : "check";
    const id = `${PORTAL_ID}->${docId}`;
    const prev = edges.get(id);
    if (prev) {
      prev.state = worst([prev.state, state]) as EdgeState;
      prev.findings.push(f.n);
      prev.findings.sort((a, b) => a - b);
      prev.pin = prev.state === "disagrees" ? (prev.findings[0] ?? null) : null;
    } else {
      edges.set(id, { id, from: PORTAL_ID, to: docId, state, source: `flag:${f.flag.flag_id}`, findings: [f.n], pin: state === "disagrees" ? f.n : null });
    }
  }
  for (const d of docs) {
    for (const c of d.checks) {
      if (!c.source) continue;
      const id = `${d.doc_id}->src:${c.source.adapter_id}`;
      const state = outcomeState(c.outcome);
      const prev = edges.get(id);
      if (prev) prev.state = worst([prev.state, state]) as EdgeState;
      else edges.set(id, { id, from: d.doc_id, to: `src:${c.source.adapter_id}`, state, source: `check:${d.doc_id}:${c.source.adapter_id}:${c.kind}`, findings: [], pin: null });
    }
  }
  return { nodes, edges: [...edges.values()], width: GRAPH_W, height: GRAPH_H };
}
