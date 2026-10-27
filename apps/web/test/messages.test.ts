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

  it("the empty queue and the forbidden page carry the exact wording", () => {
    expect(en.queue.emptyTitle + " " + en.queue.emptyBody).toBe(
      "No applications yet. Submit one from the approval portal.",
    );
    expect(en.forbidden.heading).toBe("Not assigned to you");
  });

  const values = (obj: Record<string, unknown>): string[] =>
    Object.values(obj).flatMap((v) => (v && typeof v === "object" ? values(v as Record<string, unknown>) : [String(v)]));

  it("the workbench copy has no prototype, concept, mock or demo wording and no em dashes (v0.8)", () => {
    for (const [name, messages] of [["en", en], ["hi", hi]] as const) {
      for (const text of values(messages)) {
        expect(text, `${name}: ${text}`).not.toMatch(/prototype|concept|\bmock\b|\bdemo\b|प्रोटोटाइप|नकली|मॉक|डेमो|\u2014|\u2013/i);
      }
    }
  });

  it("the old upper-case source and anchor tags are gone", () => {
    const text = JSON.stringify(en);
    expect(text).not.toContain("MOCK SOURCE");
    expect(text).not.toContain("TEST TRUST ANCHOR");
  });

  it("no copy offers an approve, reject or auto-clear action (guard rail 1)", () => {
    const text = JSON.stringify(en).toLowerCase();
    for (const banned of ["approve application", "reject application", "auto-clear", "auto clear"]) {
      expect(text).not.toContain(banned);
    }
  });
});
