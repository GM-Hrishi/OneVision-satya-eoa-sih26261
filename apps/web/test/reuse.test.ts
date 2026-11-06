import { describe, expect, it } from "vitest";
import fixture from "../src/lib/api/__fixtures__/reuse-index.dev.json";
import { buildReuseGraph, type ReuseIndex } from "../src/lib/api/k-adapters/reuse";
import { features } from "../src/lib/features";

describe("reuse graph", () => {
  const index = fixture as unknown as ReuseIndex;

  it("draws an edge per listed institution and counts how many share each artifact", () => {
    const g = buildReuseGraph(index);
    expect(g.edges.length).toBe(5);
    expect(g.nodes.filter((n) => n.type === "artifact").map((n) => n.count)).toEqual([2, 3]);
    expect(g.shared).toBe(2);
  });

  it("an artifact held by one institution is not a share, and unknown institutions draw nothing", () => {
    const g = buildReuseGraph({ institutions: [{ id: "a", name: "A" }], artifacts: [{ id: "x", kind: "stamp_serial", label: "L", institution_ids: ["a", "ghost"] }] });
    expect(g.edges).toEqual([]);
    expect(g.shared).toBe(0);
  });

  it("every edge joins existing nodes", () => {
    const g = buildReuseGraph(index);
    const ids = new Set(g.nodes.map((n) => n.id));
    for (const e of g.edges) expect(ids.has(e.from) && ids.has(e.to)).toBe(true);
  });

  it("the feature is off unless the dev fixtures flag is set", () => {
    delete process.env.NEXT_PUBLIC_UI_FIXTURES;
    expect(features.reuseGraph).toBe(false);
  });
});
