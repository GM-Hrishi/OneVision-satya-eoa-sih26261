import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";
import type { Review, ReviewDocument, ReviewFlag } from "../src/lib/demo-types";
import { EvidenceMap } from "../src/components/k/EvidenceMap";
import { Journey } from "../src/components/k/Journey";
import { buildEvidenceGraph } from "../src/lib/api/k-adapters/graph";
import { buildJourney } from "../src/lib/api/k-adapters/journey";
import en from "../messages/en.json";

const read = { status: "native", reason_code: null, variant: null, why: null, values: {}, page_count: 1, ocr_mean_confidence: null, pages: [] };
const docs = [
  { doc_id: "doc_A", title: "Affidavit 2", label: "mismatch_detected", checks: [], read },
  { doc_id: "doc_B", title: "Land deed", label: "verified", checks: [], read },
] as unknown as ReviewDocument[];
const flags = [{ flag_id: "f1", doc_id: "doc_A", rule_id: "LAND-AREA-RECON", label: "mismatch_detected", severity: "warning", why: "The sworn land area differs.", extracted_value: 3.5, expected_value: 4.5, extracted_source: { doc_label: "d" }, expected_source: { label: "e" }, regions: [], preliminary_indicator: true, disposition: null }] as unknown as ReviewFlag[];
const review = { documents: docs, flags } as unknown as Review;
const wrap = (el: ReturnType<typeof createElement>) => renderToStaticMarkup(createElement(NextIntlClientProvider, { locale: "en", messages: en } as never, el));

describe("evidence map and journey views", () => {
  const graph = buildEvidenceGraph(review);

  it("the map shows a focusable node per document, a pin on the red line, the legend with words and the same facts as text", () => {
    const html = wrap(createElement(EvidenceMap, { graph, caseId: "cas_X", findings: [{ n: 1, rule: "LAND-AREA-RECON", why: "The sworn land area differs." }] }));
    expect(html).toContain("Open Affidavit 2");
    expect(html).toContain("<title>Land deed</title>");
    for (const word of ["Agrees", "Disagrees", "Waiting", "A person must check"]) expect(html).toContain(word);
    expect(html).toContain("Portal form and Affidavit 2: Disagrees (finding 1)");
    expect(html).toContain("The sworn land area differs.");
  });

  it("with reduced motion (the server and first-paint state) no animation class is rendered", () => {
    const html = wrap(createElement(EvidenceMap, { graph, caseId: "cas_X", findings: [] })) + wrap(createElement(Journey, { rows: buildJourney(review) }));
    expect(html).not.toMatch(/\bm-(draw|pop|rise|drop|growx|ping|stamp|flash)\b/);
  });

  it("an empty map says so instead of drawing anything", () => {
    const empty = buildEvidenceGraph({ documents: docs, flags: [] } as unknown as Review);
    expect(wrap(createElement(EvidenceMap, { graph: empty, caseId: "cas_X", findings: [] }))).toContain("has no lines");
  });

  it("the journey names every step in words, per document", () => {
    const html = wrap(createElement(Journey, { rows: buildJourney(review) }));
    for (const step of ["Template recognised", "Fields read", "Rules checked", "Issuer asked", "Signature"]) expect(html).toContain(step);
    expect(html).toContain("Affidavit 2");
  });
});
