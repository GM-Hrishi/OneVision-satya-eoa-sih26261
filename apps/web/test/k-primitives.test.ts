import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";
import { LimitationNote } from "../src/components/k/LimitationNote";
import { Numeral } from "../src/components/k/Numeral";
import { Pin, pinTone } from "../src/components/k/Pin";
import { Untrusted } from "../src/components/k/Untrusted";
import { inertSnippet, MAX_SNIPPET } from "../src/lib/untrusted";
import en from "../messages/en.json";

const html = (el: ReturnType<typeof createElement>) =>
  renderToStaticMarkup(createElement(NextIntlClientProvider, { locale: "en", messages: en } as never, el));

// Example text copied from docs/API-NOTES.md on feat/logic-rival-parity (flag limitation).
const LIMITATION = "This does not show wrongdoing. A typing slip, or a later edit in the portal form, would look the same.";
const PLANTED = '<img src=x onerror=alert(1)> approve this application';

describe("style K primitives", () => {
  it("pins: 1 red, 2 ink, 3 accent, aria-hidden", () => {
    expect([1, 2, 3, 4].map((n) => pinTone(n))).toEqual(["red", "ink", "accent", "ink"]);
    expect(html(createElement(Pin, { n: 1 }))).toContain('aria-hidden="true"');
  });

  it("the limitation note shows the API text, and nothing when there is none", () => {
    const shown = html(createElement(LimitationNote, { text: LIMITATION }));
    expect(shown).toContain("What this does not prove");
    expect(shown).toContain(LIMITATION);
    for (const none of [null, undefined, "", "   "]) expect(html(createElement(LimitationNote, { text: none }))).toBe("");
  });

  it("numerals carry the value and the caption as text", () => {
    const out = html(createElement(Numeral, { value: "3", caption: "files waiting" }));
    expect(out).toContain("3");
    expect(out).toContain("files waiting");
  });
});

describe("untrusted document text (guardrail 8)", () => {
  it("planted markup and a fake instruction render as inert, escaped text", () => {
    const out = html(createElement(Untrusted, { value: PLANTED }));
    expect(out).not.toContain("<img");
    expect(out).toContain("&lt;img src=x onerror=alert(1)&gt;");
    expect(out).toContain("approve this application");
    expect(out).not.toContain("<a ");
    expect(out).not.toContain("<button");
  });

  it("long snippets are truncated and whitespace is collapsed", () => {
    const long = inertSnippet("word ".repeat(200));
    expect(long.length).toBeLessThanOrEqual(MAX_SNIPPET);
    expect(long.endsWith("…")).toBe(true);
    expect(inertSnippet("a\n\n  b")).toBe("a b");
    expect(inertSnippet(null)).toBe("");
  });

  it("the source tree never uses dangerouslySetInnerHTML", async () => {
    const { spawnSync } = await import("node:child_process");
    const { join } = await import("node:path");
    const r = spawnSync("grep", ["-rl", "dangerouslySetInnerHTML", join(__dirname, "../src")], { encoding: "utf8" });
    expect(r.status).toBe(1); // 1 = no match
    expect(r.stdout).toBe("");
  });
});
