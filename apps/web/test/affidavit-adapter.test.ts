import { describe, expect, it } from "vitest";
import type { AffidavitDiff } from "@satya/shared-types";
import { affidavitSummary, tieRows, wasCompared } from "../src/lib/api/k-adapters/affidavit";

// Counts copied from the summary example in docs/API-NOTES.md: total 24, match 23, differ 1 (declaration 9).
const decl = (no: number) => ({ no, printed_no: no, block: "core", text: `Declaration ${no}` });
const sw = (no: number) => ({ no, printed_no: no, block: "core", text: `Declaration ${no}`, page: 2, region: { x: 0, y: 0, w: 1, h: 1 }, ocr_confidence: null });
const ops = Array.from({ length: 24 }, (_, i) => ({ op: i === 8 ? "changed" : "equal", decl_no: i + 1, sworn_no: i + 1, similarity: 1, spans: [] }));
const diff = (over: object = {}) =>
  ({ expected: { declarations: Array.from({ length: 24 }, (_, i) => decl(i + 1)) }, sworn: { declarations: Array.from({ length: 24 }, (_, i) => sw(i + 1)) }, ops, comparison: { state: "compared", source: "text_layer", read: {} }, ...over }) as unknown as AffidavitDiff;

describe("affidavit summary", () => {
  it("counts from the rows when the API sends no summary", () => {
    expect(affidavitSummary(diff())).toEqual({ total: 24, match: 23, differ: 1, missing: 0, notComparable: 0, source: "counted" });
  });

  it("uses the API summary when it has the documented shape", () => {
    const api = { total: 24, match: 23, differ: 1, missing_in_sworn: 0, not_comparable: 0, added_in_sworn: 0, differing: [] };
    expect(affidavitSummary(diff({ summary: api }))).toMatchObject({ total: 24, match: 23, differ: 1, source: "api" });
    expect(affidavitSummary(diff({ summary: { total: "x" } })).source).toBe("counted");
  });

  it("a copy that was not compared never counts anything as a match", () => {
    for (const comparison of [undefined, { state: "not_compared", source: "scan_read", read: {} }]) {
      const s = affidavitSummary(diff({ comparison }));
      expect([s.match, s.differ, s.notComparable]).toEqual([0, 0, 24]);
    }
    expect(wasCompared(diff())).toBe(true);
  });

  it("counts removed declarations as missing in the sworn copy, not as differing", () => {
    const o = ops.map((x, i) => (i === 3 ? { ...x, op: "removed", sworn_no: null } : x));
    expect(affidavitSummary(diff({ ops: o }))).toMatchObject({ match: 22, differ: 1, missing: 1 });
  });
});

describe("tie rows", () => {
  it("pairs sworn and portal text per op and keeps the API's own words", () => {
    const rows = tieRows(diff());
    expect(rows.length).toBe(24);
    expect(rows[8]).toMatchObject({ no: 9, op: "changed", sworn: "Declaration 9", portal: "Declaration 9", swornPage: 2 });
  });

  it("a removed declaration has no sworn text; an added one has no portal text", () => {
    const rows = tieRows(diff({ ops: [{ op: "removed", decl_no: 3, sworn_no: null, similarity: 0, spans: [] }, { op: "added", decl_no: null, sworn_no: 5, similarity: 0, spans: [] }] }));
    expect(rows[0]).toMatchObject({ sworn: null, portal: "Declaration 3" });
    expect(rows[1]).toMatchObject({ sworn: "Declaration 5", portal: null });
  });
});
