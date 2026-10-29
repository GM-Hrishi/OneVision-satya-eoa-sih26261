import { readFileSync } from "node:fs";
import { join } from "node:path";
import { createTranslator } from "next-intl";
import { describe, expect, it } from "vitest";

const en = JSON.parse(readFileSync(join(__dirname, "..", "messages", "en.json"), "utf8"));
const t = createTranslator({ locale: "en", messages: en, namespace: "demo.ocr" });
const values = { count: 2, pages: "1, 2", confidence: 91, threshold: 80, max_pages: 50 };

describe("OCR reason sentences (B-28)", () => {
  it("every variant formats with the numbers the API sends and ends as a sentence", () => {
    for (const variant of Object.keys(en.demo.ocr.why)) {
      const text = t(`why.${variant}` as never, values as never);
      expect(text, variant).toMatch(/\.$/);
      expect(text, variant).not.toMatch(/[{}—]/);
    }
  });

  it("the scan sentence says which pages were read and how confidently", () => {
    expect(t("why.scan_read" as never, values as never)).toContain("Pages 1, 2 were read by OCR (confidence 91%)");
    expect(t("why.scan_read" as never, { ...values, count: 1, pages: "2" } as never)).toContain("Page 2 was read by OCR");
  });
});
