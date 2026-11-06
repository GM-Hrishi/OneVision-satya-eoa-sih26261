// Style K copy lint (prompt guardrail 3 and 9): no loaded words, no em dashes, no percentages, no "prototype", "demo",
// "concept" or "MOCK" in what an official reads. Runs over every UI string, English and Hindi.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import en from "../messages/en.json";
import hi from "../messages/hi.json";

const LOADED = /\b(forged|forgery|fake|fraud|fraudulent|tampered|tampering|cheat|cheating)\b/i;
const EM_DASH = /—/;
const PERCENT = /\d\s?%|%\s?\d/;
const WORKBENCH_BANNED = /\b(prototype|demo|concept|MOCK)\b/;

const values = (obj: Record<string, unknown>, prefix = ""): [string, string][] =>
  Object.entries(obj).flatMap(([k, v]) =>
    v && typeof v === "object" ? values(v as Record<string, unknown>, `${prefix}${k}.`) : [[`${prefix}${k}`, String(v)] as [string, string]],
  );

describe("copy lint", () => {
  for (const [name, messages] of [["en", en], ["hi", hi]] as const) {
    it(`${name}: no loaded words, em dashes or percentages in any string`, () => {
      for (const [key, text] of values(messages)) {
        expect(LOADED.test(text), `${name} ${key}: ${text}`).toBe(false);
        expect(EM_DASH.test(text), `${name} ${key} has an em dash`).toBe(false);
        // "200% text size" on the accessibility page is a zoom level, not a statistic.
        if (!key.startsWith("accessibility.")) expect(PERCENT.test(text), `${name} ${key} has a percentage`).toBe(false);
      }
    });
  }

  it("English strings never say prototype, demo, concept or MOCK (the separate mock portal keeps its own strip)", () => {
    for (const [key, text] of values(en)) expect(WORKBENCH_BANNED.test(text), `${key}: ${text}`).toBe(false);
  });

  it("style K sources use no border-left accent, no gradient and no raw hex colour outside tokens", () => {
    const walk = (dir: string): string[] =>
      readdirSync(dir).flatMap((n) => {
        const p = join(dir, n);
        return statSync(p).isDirectory() ? walk(p) : p.endsWith(".css") ? [p] : [];
      });
    const k = [...walk(join(__dirname, "../src/components/k")), join(__dirname, "../src/styles/k.css"), join(__dirname, "../src/styles/motion.css"), join(__dirname, "../src/components/shell/AppShell.module.css")];
    for (const path of k) {
      const css = readFileSync(path, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
      expect(/border-left\s*:/.test(css), `${path} uses border-left`).toBe(false);
      expect(/gradient\(/.test(css), `${path} uses a gradient`).toBe(false);
      expect(/#[0-9a-fA-F]{3,8}\b/.test(css), `${path} has a raw hex colour`).toBe(false);
    }
  });
});
