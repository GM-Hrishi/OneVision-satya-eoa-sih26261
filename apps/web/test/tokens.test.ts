import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const app = join(__dirname, "..");

describe("design tokens", () => {
  it("tokens.css is generated from tokens.json and covers every UI spec §8 colour", () => {
    const out = execFileSync("node", ["scripts/gen-tokens.mjs", "--check"], { cwd: app }).toString();
    expect(out).toContain("up to date");
  });

  it("defines the six label colours and three risk colours", () => {
    const css = readFileSync(join(app, "src/styles/tokens.css"), "utf8");
    for (const name of ["verified", "mismatch", "expired", "pending", "source-unavailable", "manual-review"]) {
      expect(css).toContain(`--color-label-${name}:`);
    }
    for (const band of ["high", "medium", "low"]) expect(css).toContain(`--color-risk-${band}:`);
  });

  it("does not use Inter anywhere", () => {
    expect(readFileSync(join(app, "src/styles/tokens.json"), "utf8")).not.toMatch(/\bInter\b/);
  });
});
