import { describe, expect, it } from "vitest";
import ok from "../src/lib/api/__fixtures__/replay-check.ok.json";
import verify from "../src/lib/api/__fixtures__/audit-verify.ok.json";
import { fromReplayCheck } from "../src/lib/api/k-adapters/replay";
import { fromVerify } from "../src/lib/api/k-adapters/chain";
import { uiFixtures } from "../src/lib/fixtures";

describe("replay-check adapter", () => {
  it("reads the documented example as reproduced, with Same rows", () => {
    const vm = fromReplayCheck(ok);
    expect(vm?.reproduced).toBe(true);
    expect(vm?.rows.map((r) => [r.key, r.same])).toEqual([["findings", true], ["ruleset", true], ["as_of", true]]);
  });

  it("a differing digest is Different even if a body claims otherwise", () => {
    const lying = { ...ok, digest_replayed: "0".repeat(64), reproduced_identically: true };
    const vm = fromReplayCheck(lying);
    expect(vm?.reproduced).toBe(false);
    expect(vm?.rows[0]?.same).toBe(false);
  });

  it("carries the API's reasons and refuses a body of the wrong shape", () => {
    expect(fromReplayCheck({ ...ok, reproduced_identically: false, reasons: ["first changed entry 4"] })?.reasons).toEqual(["first changed entry 4"]);
    expect(fromReplayCheck({})).toBeNull();
    expect(fromReplayCheck(null)).toBeNull();
  });

  it("the audit verify example reads as an intact chain of 7 entries", () => {
    expect(fromVerify(verify)).toMatchObject({ state: "intact", entries: 7 });
  });

  it("fixtures are off unless the dev flag is set, and never in production", () => {
    const prev = { flag: process.env.NEXT_PUBLIC_UI_FIXTURES, env: process.env.NODE_ENV };
    try {
      delete process.env.NEXT_PUBLIC_UI_FIXTURES;
      expect(uiFixtures()).toBe(false);
      process.env.NEXT_PUBLIC_UI_FIXTURES = "1";
      (process.env as Record<string, string>).NODE_ENV = "production";
      expect(uiFixtures()).toBe(false);
      (process.env as Record<string, string>).NODE_ENV = "development";
      expect(uiFixtures()).toBe(true);
    } finally {
      if (prev.flag === undefined) delete process.env.NEXT_PUBLIC_UI_FIXTURES;
      else process.env.NEXT_PUBLIC_UI_FIXTURES = prev.flag;
      (process.env as Record<string, string | undefined>).NODE_ENV = prev.env;
    }
  });
});
