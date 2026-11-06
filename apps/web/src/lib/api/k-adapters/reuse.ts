// VISUAL 6: reuse graph. Pure builder from the (not yet existing) cross-case fingerprint index. Edges exist only where
// the index lists an institution under an artifact; the badge is the number of institutions listed. An artifact that
// only one institution has is not a "share" and is left out.
export type ArtifactKind = "stamp_serial" | "signature_image";

export interface ReuseIndex {
  institutions: { id: string; name: string }[];
  artifacts: { id: string; kind: ArtifactKind; label: string; institution_ids: string[] }[];
}

export interface ReuseNode {
  id: string;
  type: "institution" | "artifact";
  label: string;
  kind: ArtifactKind | null;
  count: number;
  x: number;
  y: number;
}
export interface ReuseEdge {
  id: string;
  from: string;
  to: string;
}
export interface ReuseGraph {
  nodes: ReuseNode[];
  edges: ReuseEdge[];
  shared: number;
  height: number;
}

const ROW = 86;
export const REUSE_W = 900;

export function buildReuseGraph(index: ReuseIndex): ReuseGraph {
  const known = new Set(index.institutions.map((i) => i.id));
  const artifacts = index.artifacts
    .map((a) => ({ ...a, ids: [...new Set(a.institution_ids.filter((id) => known.has(id)))] }))
    .filter((a) => a.ids.length > 1);
  const used = new Set(artifacts.flatMap((a) => a.ids));
  const institutions = index.institutions.filter((i) => used.has(i.id));
  const rows = Math.max(institutions.length, artifacts.length, 1);
  const nodes: ReuseNode[] = [
    ...institutions.map((i, n): ReuseNode => ({ id: i.id, type: "institution", label: i.name, kind: null, count: 0, x: 150, y: 60 + n * ROW })),
    ...artifacts.map((a, n): ReuseNode => ({ id: a.id, type: "artifact", label: a.label, kind: a.kind, count: a.ids.length, x: 700, y: 60 + n * ROW })),
  ];
  const edges = artifacts.flatMap((a) => a.ids.map((id): ReuseEdge => ({ id: `${id}->${a.id}`, from: id, to: a.id })));
  return { nodes, edges, shared: artifacts.length, height: 60 + rows * ROW };
}
