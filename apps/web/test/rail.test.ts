import { describe, expect, it } from "vitest";
import { isCurrent } from "../src/components/shell/RailNav";
import { RAIL, UTILITY } from "../src/lib/rail";

describe("rail", () => {
  it("marks exactly one RB item current per page", () => {
    const items = RAIL.RB ?? [];
    const current = (path: string) => items.filter((i) => isCurrent(i.href, path));
    expect(current("/rb-queue").map((i) => i.labelKey)).toEqual(["queue"]);
    expect(current("/overview").map((i) => i.labelKey)).toEqual(["overview"]);
    expect(current("/help")).toEqual([]);
  });

  it("lists only routes that exist in this build (no dead navigation)", () => {
    const built = new Set(["/overview", "/rb-queue", "/alerts", "/audit", "/help", "/accessibility"]);
    for (const item of [...(RAIL.RB ?? []), ...(RAIL.AU ?? []), ...UTILITY]) {
      expect(built.has(new URL(item.href, "https://x.invalid").pathname), item.href).toBe(true);
    }
  });
});

describe("breadcrumbs", () => {
  it("gives case pages a trail back to the queue", async () => {
    const { crumbsFor } = await import("../src/lib/rail");
    expect(crumbsFor("/case/cas_01JD3M5A00000000000000DT03/affidavit")).toEqual([
      { labelKey: "queue", href: "/rb-queue" },
      { labelKey: "affidavit" },
    ]);
    expect(crumbsFor("/case/cas_01JD3M5A00000000000000DT03/verification")).toEqual([
      { labelKey: "queue", href: "/rb-queue" },
      { labelKey: "verification" },
    ]);
    expect(crumbsFor("/help")).toEqual([{ labelKey: "help" }]);
    expect(crumbsFor("/nowhere")).toEqual([]);
  });
});
