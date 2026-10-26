import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const load = (name: string) => JSON.parse(readFileSync(join(__dirname, "..", "messages", name), "utf8"));
const keys = (obj: Record<string, unknown>, prefix = ""): string[] =>
  Object.entries(obj).flatMap(([k, v]) =>
    v && typeof v === "object" ? keys(v as Record<string, unknown>, `${prefix}${k}.`) : [`${prefix}${k}`],
  );

describe("messages", () => {
  const en = load("en.json");
  const hi = load("hi.json");
  const review = load("hi.review.json");

  it("English and Hindi have exactly the same keys", () => {
    expect(keys(hi).sort()).toEqual(keys(en).sort());
  });

  it("every Hindi review entry points at a real key and is marked [VERIFY]", () => {
    const all = new Set(keys(en));
    for (const [key, note] of Object.entries(review)) {
      if (key === "_note") continue;
      expect(all.has(key), key).toBe(true);
      expect(String(note)).toContain("[VERIFY]");
    }
  });

  it("the prototype strip carries the exact wording", () => {
    expect(en.shell.prototypeStrip).toBe("Prototype · connected to a mock approval portal · synthetic data only");
    expect(en.queue.emptyTitle + " " + en.queue.emptyBody).toBe(
      "No applications yet. Submit one from the mock portal.",
    );
    expect(en.forbidden.heading).toBe("Not assigned to you");
  });

  it("no copy offers an approve, reject or auto-clear action (guard rail 1)", () => {
    const text = JSON.stringify(en).toLowerCase();
    for (const banned of ["approve application", "reject application", "auto-clear", "auto clear"]) {
      expect(text).not.toContain(banned);
    }
  });
});
