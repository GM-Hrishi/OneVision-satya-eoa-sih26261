import { describe, expect, it } from "vitest";
import type { Review, ReviewDocument, ReviewFlag } from "../src/lib/demo-types";
import { buildEvidenceGraph } from "../src/lib/api/k-adapters/graph";
import { buildJourney } from "../src/lib/api/k-adapters/journey";

const read = { status: "native", reason_code: null, variant: null, why: null, values: {}, page_count: 1, ocr_mean_confidence: null, pages: [] };
const doc = (id: string, over: Partial<ReviewDocument> = {}): ReviewDocument =>
  ({ doc_id: id, slot: "s", title: `Doc ${id}`, sha256: "a", bytes: 1, label: "verified", source: { channel: "x", adapter_mode: "mock" }, issuer_sig: null, uploader_sig: null, checks: [], manual_task: false, checked_at: "t", read, ...over }) as ReviewDocument;
const flag = (id: string, docId: string | null, over: object = {}): ReviewFlag =>
  ({ flag_id: id, doc_id: docId, rule_id: "R", label: "mismatch_detected", severity: "warning", extracted_value: 1, expected_value: 2, value_unit: null, page: 1, regions: [], why: "w", extracted_source: { doc_label: "d", page: 1 }, expected_source: { label: "e" }, preliminary_indicator: true, disposition: null, ...over }) as unknown as ReviewFlag;
const source = (outcome: string, adapter = "ad1") => ({ kind: "issuer", outcome, reason_code: "X", source: { adapter_id: adapter, mode: "mock", name: "Simulated registry" } });

const review = (documents: ReviewDocument[], flags: ReviewFlag[]) => ({ documents, flags }) as unknown as Review;

describe("buildEvidenceGraph", () => {
  it("draws no edge when nothing relates two things", () => {
    const g = buildEvidenceGraph(review([doc("a"), doc("b")], []));
    expect(g.edges).toEqual([]);
    expect(g.nodes.map((n) => n.id)).toEqual(["portal", "a", "b"]);
  });

  it("every edge has a source and points at existing nodes", () => {
    const g = buildEvidenceGraph(review([doc("a", { checks: [source("verified")] as never }), doc("b")], [flag("f1", "a"), flag("f2", "b", { label: "manual_review_required" }), flag("f3", null), flag("f4", "gone")]));
    const ids = new Set(g.nodes.map((n) => n.id));
    expect(g.edges.length).toBe(3);
    for (const e of g.edges) {
      expect(e.source).toMatch(/^(flag|check):/);
      expect(ids.has(e.from) && ids.has(e.to)).toBe(true);
    }
  });

  it("a mismatch is a red edge with the lowest finding as its pin; a manual-review flag is a person-must-check edge", () => {
    const g = buildEvidenceGraph(review([doc("a"), doc("b")], [flag("f1", "a"), flag("f2", "a", { label: "manual_review_required", severity: "info" }), flag("f3", "b", { label: "manual_review_required" })]));
    const a = g.edges.find((e) => e.to === "a");
    const b = g.edges.find((e) => e.to === "b");
    expect(a).toMatchObject({ state: "disagrees", pin: 1 });
    expect(a?.findings.length).toBe(2);
    expect(b).toMatchObject({ state: "check", pin: null });
  });

  it("source checks relate a document to its issuer: verified agrees, unavailable waits", () => {
    const g = buildEvidenceGraph(review([doc("a", { checks: [source("verified")] as never }), doc("b", { checks: [source("source_unavailable")] as never })], []));
    expect(g.edges.map((e) => e.state).sort()).toEqual(["agrees", "waiting"]);
    expect(g.nodes.filter((n) => n.kind === "issuer").length).toBe(1);
  });
});

describe("buildJourney", () => {
  it("an unreadable file stops at fields read and later steps do not pretend to have run", () => {
    const rows = buildJourney(review([doc("a", { label: "manual_review_required", read: { ...read, status: "blocked", reason_code: "DOC_UNREADABLE", why: "This file could not be read." } as never })], []));
    expect(rows[0]?.stoppedAt).toBe("template");
    expect(rows[0]?.steps.rules).toBe("waiting");
    expect(rows[0]?.stopReasonText).toBe("This file could not be read.");
  });

  it("an unanswered source stops at the issuer step", () => {
    const rows = buildJourney(review([doc("a", { label: "source_unavailable", checks: [source("source_unavailable")] as never })], []));
    expect(rows[0]).toMatchObject({ stoppedAt: "issuer", stopReasonKey: "source" });
  });

  it("a clean document has no stop and every applicable step agrees", () => {
    const rows = buildJourney(review([doc("a", { checks: [source("verified")] as never })], []));
    expect(rows[0]?.stoppedAt).toBeNull();
    expect(rows[0]?.steps).toMatchObject({ template: "agrees", fields: "agrees", rules: "agrees", issuer: "agrees" });
  });
});
