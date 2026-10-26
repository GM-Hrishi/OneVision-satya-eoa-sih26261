import { describe, expect, it } from "vitest";
import { isCurrent } from "../src/components/shell/RailNav";
import { RAIL, UTILITY } from "../src/lib/rail";

describe("rail", () => {
  it("marks exactly one RB item current per page", () => {
    const items = RAIL.RB ?? [];
    const current = (path: string, view: string | null) => items.filter((i) => isCurrent(i.href, path, view));
    expect(current("/rb-queue", null).map((i) => i.labelKey)).toEqual(["queue"]);
    expect(current("/rb-queue", "overview").map((i) => i.labelKey)).toEqual(["overview"]);
    expect(current("/help", null)).toEqual([]);
  });

  it("lists only routes that exist in this build (no dead navigation)", () => {
    const built = new Set(["/rb-queue", "/help", "/accessibility"]);
    for (const item of [...(RAIL.RB ?? []), ...UTILITY]) {
      expect(built.has(new URL(item.href, "https://x.invalid").pathname), item.href).toBe(true);
    }
  });
});
