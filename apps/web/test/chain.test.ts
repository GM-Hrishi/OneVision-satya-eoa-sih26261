import { describe, expect, it } from "vitest";
import { fromAudit, fromVerify } from "../src/lib/api/k-adapters/chain";

// Example payloads copied from docs/API-NOTES.md on feat/logic-rival-parity (GET /v1/audit/verify).
const VERIFY = { checked_at: "2026-11-06T09:00:00+00:00", entries: 7, first_bad_entry: null, method: "sha256(prev_hash || payload_sha256 || at), recomputed for every row", status: "intact" };

describe("chain status adapter", () => {
  it("reads the verify answer", () => {
    expect(fromVerify(VERIFY)).toEqual({ state: "intact", entries: 7, firstBadEntry: null, checkedAt: "2026-11-06T09:00:00+00:00", source: "verify" });
    expect(fromVerify({ ...VERIFY, status: "broken", first_bad_entry: 4 })?.firstBadEntry).toBe(4);
  });

  it("reads the chain block of /v1/audit on main", () => {
    const s = fromAudit({ chain: { ok: false, rows: 9, broken_at: 5, reason: "x", recomputed_at: "t", method: "m" }, entries: [] });
    expect(s).toMatchObject({ state: "broken", entries: 9, firstBadEntry: 5, source: "audit" });
  });

  it("returns null (chip hidden) for anything else, never a guess", () => {
    expect(fromVerify(null)).toBeNull();
    expect(fromVerify({ status: "maybe" })).toBeNull();
    expect(fromAudit({ entries: [] })).toBeNull();
    expect(fromAudit({ chain: { rows: 3 } })).toBeNull();
  });
});
