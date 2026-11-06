import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { MAX_STAGGER_S, MOTIONS, motionClass, prefersReducedMotion, staggerDelay } from "../src/lib/motion";

const win = (matches: boolean) => ({ matchMedia: (q: string) => ({ matches: q.includes("prefers-reduced-motion") && matches }) });

describe("style K motion", () => {
  it("animation classes are absent when prefers-reduced-motion matches", () => {
    const reduced = prefersReducedMotion(win(true));
    expect(reduced).toBe(true);
    for (const m of MOTIONS) expect(motionClass(m, reduced)).toBe("");
  });

  it("animation classes are present when motion is allowed", () => {
    const reduced = prefersReducedMotion(win(false));
    for (const m of MOTIONS) expect(motionClass(m, reduced)).toBe(`m-${m}`);
  });

  it("without a browser (server render) motion is off", () => {
    expect(prefersReducedMotion({})).toBe(true);
  });

  it("the stagger of one view never exceeds the cap", () => {
    for (const n of [2, 5, 12, 60]) {
      const last = Number.parseFloat(staggerDelay(n - 1, n));
      expect(last).toBeLessThanOrEqual(MAX_STAGGER_S);
    }
    expect(staggerDelay(0, 1)).toBe("0s");
  });

  it("motion.css defines the eight primitives, zeroes them under reduced motion and never rests on a from-state", () => {
    const css = readFileSync(join(__dirname, "../src/styles/motion.css"), "utf8");
    for (const m of MOTIONS) {
      expect(css).toContain(`.m-${m} {`);
      expect(css).toContain(`@keyframes k-${m}`);
    }
    expect(css).toMatch(/prefers-reduced-motion: reduce[\s\S]*animation: none/);
    expect(css).toMatch(/--ease-k/);
    expect(css).not.toMatch(/fill-mode: (both|forwards)/);
  });
});
