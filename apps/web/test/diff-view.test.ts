// B-43 D1: the Affidavit diff page says "matches" only when the comparison really ran on a text
// layer and the structure check is complete. A scan, or a missing state, gets the not-compared notice.
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createTranslator, NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import en from "../messages/en.json";

vi.mock("next-intl/server", () => ({
  getTranslations: async (namespace: string) =>
    createTranslator({ locale: "en", messages: en as never, namespace: namespace as never }),
}));

const { DiffView } = await import("../src/components/diff/DiffView");

type Diff = Parameters<typeof DiffView>[0]["diff"];

const read = (over: Record<string, unknown> = {}) => ({
  status: "native",
  reason_code: null,
  variant: null,
  values: {},
  ocr_mean_confidence: null,
  ...over,
});

function makeDiff(over: Record<string, unknown> = {}): Diff {
  const structure = {
    category_line: { expected: ["Engineering"], found: ["Engineering"], state: "present", page: 1 },
    core: { expected: 19, found: 19 },
    existing_institute: { expected: 5, found: 5 },
    extra_blocks: [],
  };
  return {
    case: { case_id: "cas_01JD3M5A00000000000000DT13", application_id: "1-90000013113", ay: "2026-27" },
    doc_id: "doc_x",
    engine_version: "0.1.0",
    ruleset_version: "r",
    advisory: true,
    expected: {
      template_id: "aff2-portal-2024-27",
      template_year: "2024-27",
      aid: "1-90000013113",
      category_list: ["Engineering"],
      declarations: [{ no: 1, printed_no: 1, block: "core", text: "x" }],
    },
    sworn: {
      page_count: 4,
      sha256: "0".repeat(64),
      template_match: true,
      text_source: "text_layer",
      ocr_mean_confidence: null,
      issuer_sig: null,
      uploader_sig: null,
      category_list_found: ["Engineering"],
      declarations: [],
    },
    normalisation: { whitespace: true, strike_through_resolved: 0, names_substituted: true, hyphens_rejoined: 0, date_order: "DMY", date_order_fallbacks: 0 },
    options: [],
    ops: [],
    structure,
    tables: [],
    stamp: null,
    chronology: null,
    pending: [
      { section: "stamp", module: "M6", promise: "P-4" },
      { section: "chronology", module: "M6", promise: "P-4" },
      { section: "signatures", module: "M6", promise: "P-4" },
    ],
    flags: [],
    comparison: { state: "compared", source: "text_layer", read: read() },
    ...over,
  } as unknown as Diff;
}

async function page(diff: Diff): Promise<string> {
  const element = await DiffView({ diff, showAll: false, allHref: "?all=1", changedHref: "?", verificationHref: "/v" });
  return renderToStaticMarkup(
    createElement(NextIntlClientProvider, { locale: "en", messages: en } as never, element),
  );
}

const scanRead = (variant: string, over: Record<string, unknown> = {}) =>
  read({ status: variant === "scan_read" ? "ocr_read" : "blocked", reason_code: "SCAN_IMAGE_ONLY", variant, ...over });

const emptyStructure = {
  category_line: { expected: ["Engineering"], found: [], state: "missing" },
  core: { expected: 19, found: 0 },
  existing_institute: { expected: 5, found: 0 },
  extra_blocks: [],
};

describe("Affidavit diff: truthful comparison state", () => {
  it("says the copy matches only for a compared text layer with a complete structure", async () => {
    const html = await page(makeDiff());
    expect(html).toContain("The sworn copy matches the portal draft");
    expect(html).toContain("Every declaration matches the portal draft");
    expect(html).not.toContain("Not compared");
    expect(html).toContain("PDF text layer");
  });

  it.each([
    ["scan_read", "Scan, read by OCR (confidence 93%)"],
    ["low_confidence", "Scan, read by OCR but not reliable"],
    ["scan_not_attempted", "Scan, not read by OCR"],
    ["scan_timeout", "OCR did not finish in the time allowed"],
    ["unavailable", "OCR engine not available on this system"],
  ])("never says matches for a scan (%s) and explains that nothing was compared", async (variant, source) => {
    const sourceKey = {
      scan_read: "scan_read",
      low_confidence: "scan_unreliable",
      scan_not_attempted: "scan_not_read",
      scan_timeout: "scan_timeout",
      unavailable: "ocr_unavailable",
    }[variant as string];
    const html = await page(
      makeDiff({
        structure: emptyStructure,
        sworn: { ...makeDiff().sworn, template_match: false, text_source: "ocr" },
        comparison: {
          state: "not_compared",
          source: sourceKey,
          read: scanRead(variant, { values: { confidence: 93, threshold: 70, pages: "1", count: 1 }, ocr_mean_confidence: 0.93 }),
        },
      }),
    );
    expect(html).not.toMatch(/matches the portal draft/i);
    expect(html).not.toContain("No declaration differs");
    expect(html).not.toContain("DOES NOT MATCH");
    expect(html).toContain("Not compared");
    expect(html).toMatch(/official must/);
    expect(html).toContain(source);
    expect(html).toContain("This is not a match");
  });

  it("treats a missing comparison state as not compared", async () => {
    const diff = makeDiff();
    delete (diff as unknown as Record<string, unknown>).comparison;
    const html = await page(diff);
    expect(html).not.toMatch(/matches the portal draft/i);
    expect(html).toContain("Not compared");
  });

  it("never says matches when the structure is incomplete on a text-layer file", async () => {
    const html = await page(makeDiff({ structure: { ...makeDiff().structure, core: { expected: 19, found: 17 } } }));
    expect(html).not.toMatch(/matches the portal draft/i);
    expect(html).not.toContain("No declaration differs from");
    expect(html).toContain("structure check did not find every declaration");
  });
});
