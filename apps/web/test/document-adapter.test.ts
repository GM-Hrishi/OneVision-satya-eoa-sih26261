import { describe, expect, it } from "vitest";
import type { AffidavitChronology, CaseVerificationDocument } from "@satya/shared-types";
import { chronologyItems, compareRows } from "../src/lib/api/k-adapters/document";

describe("document evidence adapter", () => {
  it("lists each compared field with the submitted value, the record value and a simulated-source flag", () => {
    const rows = compareRows({
      checks: [
        { kind: "source_lookup", outcome: "mismatch_detected", reason_code: "X", source: { adapter_id: "shcil-estamp-mock", mode: "mock", name: "e-Stamp lookup" }, field_diff: [{ field: "serial", submitted: "A-1", source: "A-2" }, { field: "duty", submitted: 100, source: null }] },
        { kind: "format", outcome: "verified", reason_code: "Y" },
      ],
    } as unknown as CaseVerificationDocument);
    expect(rows.map((r) => [r.field, r.submitted, r.record, r.simulated])).toEqual([["serial", "A-1", "A-2", true], ["duty", "100", "", true]]);
    expect(rows[0]?.sourceName).toBe("e-Stamp lookup");
  });

  it("no checks, no rows", () => {
    expect(compareRows({ checks: undefined } as unknown as CaseVerificationDocument)).toEqual([]);
  });

  it("keeps only the dates that exist, in the defined order", () => {
    const items = chronologyItems({ application_date: "2026-10-01", stamp_date: "2026-10-02", notary_date: null, dsc_date: undefined, upload_date: "2026-10-05", order_ok: true } as unknown as AffidavitChronology);
    expect(items.map((i) => i.key)).toEqual(["application_date", "stamp_date", "upload_date"]);
    expect(chronologyItems(null)).toEqual([]);
  });
});
