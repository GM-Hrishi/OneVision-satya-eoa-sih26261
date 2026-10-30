// B-43 D2: no build codes, module names or roadmap promises in anything an official reads.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import en from "../messages/en.json";
import hi from "../messages/hi.json";

const BANNED: [string, RegExp][] = [
  ["module code (M3, M6, M11 ...)", /\bM\d{1,2}\b/],
  ["issue code (P-4, P-10 ...)", /\bP-\d+\b/],
  ["build slice", /\bSlice\b/],
  ["roadmap promise", /\barrives? with\b|\bwill arrive\b|\bcoming soon\b/i],
  ["unfinished page", /not evaluated on this page yet/i],
  ["future tense filler", /\bto be\b/i],
  ["planned", /\bplanned\b/i],
];

const values = (obj: Record<string, unknown>, prefix = ""): [string, string][] =>
  Object.entries(obj).flatMap(([k, v]) =>
    v && typeof v === "object"
      ? values(v as Record<string, unknown>, `${prefix}${k}.`)
      : [[`${prefix}${k}`, String(v)] as [string, string]],
  );

function sources(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return sources(path);
    return /\.(tsx?|css)$/.test(name) && !/\.css$/.test(name) ? [path] : [];
  });
}

/** Source text without comments; SVG path data in the icon files is not wording. */
function code(path: string): string {
  return readFileSync(path, "utf8")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:\w])\/\/.*$/gm, "$1");
}

describe("workbench wording", () => {
  for (const [name, messages] of [["en", en], ["hi", hi]] as const) {
    it(`${name} messages carry no build code or roadmap promise`, () => {
      for (const [key, text] of values(messages)) {
        for (const [what, pattern] of BANNED) {
          expect(pattern.test(text), `${name} ${key} has a ${what}: ${text}`).toBe(false);
        }
      }
    });
  }

  it("components and pages carry none either (comments and icon paths aside)", () => {
    const skip = /(Icon|SortIndicator)\.tsx$/;
    for (const path of sources(join(__dirname, "..", "src"))) {
      if (skip.test(path)) continue;
      const text = code(path);
      for (const [what, pattern] of BANNED) {
        expect(pattern.test(text), `${path} has a ${what}`).toBe(false);
      }
    }
  });
});
