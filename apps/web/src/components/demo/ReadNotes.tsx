// How a file was read (B-28): the fixed "why" sentence for a scan or an unreadable file, and one
// line per scanned page with the OCR confidence of that page. Advisory: OCR text is never a verdict.
import { getTranslations } from "next-intl/server";
import diff from "@/components/diff/DiffView.module.css";
import type { ReadSummary } from "@/lib/demo-types";

export async function ReadNotes({ read }: { read: ReadSummary }) {
  const t = await getTranslations("demo.ocr");
  if (!read.reason_code || !read.variant) return null;
  const values = { max_pages: 50, ...read.values } as Record<string, string | number>;
  const scanned = read.pages.filter((p) => p.kind === "image_only" || p.kind === "skipped");
  return (
    <>
      <p className={diff.note}>{t(`why.${read.variant}` as never, values as never)}</p>
      {scanned.length > 0 ? (
        <ul className={diff.note} aria-label={t("heading")}>
          {scanned.slice(0, 12).map((p) => (
            <li key={p.page}>
              {p.kind === "skipped"
                ? t("skippedPage", { page: p.page })
                : p.ocr_confidence === undefined
                  ? t("scanPageNotRead", { page: p.page })
                  : p.ocr_words === 0
                    ? t("scanPageEmpty", { page: p.page })
                    : t("scanPage", { page: p.page, confidence: Math.round(p.ocr_confidence * 100) })}
            </li>
          ))}
        </ul>
      ) : null}
    </>
  );
}
