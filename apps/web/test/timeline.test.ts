import { describe, expect, it } from "vitest";
import type { QueueRow } from "../src/lib/demo-types";
import { buildTimeline } from "../src/lib/api/k-adapters/timeline";

const ASOF = "2026-11-06T09:00:00+00:00";
const row = (id: string, submitted: string, band: "high" | "medium" | "low" = "high") =>
  ({ case_id: `cas_${id}`, application_id: `1-9000000${id}`, risk_band: band, submitted_at: submitted }) as unknown as QueueRow;

describe("buildTimeline", () => {
  it("places each case at its days waiting and stacks dots that share a day", () => {
    const t = buildTimeline([row("4217", "2026-11-04T09:00:00+00:00"), row("4218", "2026-11-04T10:00:00+00:00"), row("4219", "2026-11-01T09:00:00+00:00", "low")], ASOF);
    expect(t.points.map((p) => [p.tail, p.days, p.stack])).toEqual([["4217", 2, 0], ["4218", 1, 0], ["4219", 5, 0]]);
    expect(t.maxDays).toBe(5);
  });

  it("identical days stack upward", () => {
    const t = buildTimeline([row("0001", "2026-11-04T09:00:00+00:00"), row("0002", "2026-11-04T08:30:00+00:00")], ASOF);
    expect(t.points.map((p) => p.stack)).toEqual([0, 1]);
    expect(t.maxStack).toBe(1);
  });

  it("marks the longest wait, but not when nobody has waited", () => {
    const t = buildTimeline([row("0001", "2026-11-01T09:00:00+00:00"), row("0002", "2026-11-05T09:00:00+00:00")], ASOF);
    expect(t.points.map((p) => p.longest)).toEqual([true, false]);
    expect(buildTimeline([row("0001", ASOF)], ASOF).points[0]?.longest).toBe(false);
  });

  it("skips rows whose date cannot be read and handles an empty list", () => {
    expect(buildTimeline([row("0001", "nope")], ASOF).points).toEqual([]);
    expect(buildTimeline([], ASOF)).toEqual({ points: [], maxDays: 0, maxStack: 0 });
  });
});

import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { NextIntlClientProvider } from "next-intl";
import { QueueTimeline } from "../src/components/k/QueueTimeline";
import en from "../messages/en.json";

describe("QueueTimeline", () => {
  const html = (rows: QueueRow[]) =>
    renderToStaticMarkup(createElement(NextIntlClientProvider, { locale: "en", messages: en } as never, createElement(QueueTimeline, { timeline: buildTimeline(rows, ASOF) })));

  it("shows a band letter in each circle, the last four digits, an accessible name and the longest-wait note", () => {
    const out = html([row("4217", "2026-11-01T09:00:00+00:00"), row("4218", "2026-11-05T09:00:00+00:00", "medium")]);
    expect(out).toContain(">H<");
    expect(out).toContain(">M<");
    expect(out).toContain(">4217<");
    expect(out).toContain("Application 1-90000004217, High attention, waiting 5 days");
    expect(out).toContain("Waited longest");
    expect(out).toContain("does not say which file to decide first");
  });

  it("says so when there is nothing to place", () => {
    expect(html([])).toContain("No files to place on the timeline.");
  });
});
