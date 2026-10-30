// A reason shown to an official (B-43): the plain sentence first, the code second as a small
// monospace label for auditors. The code alone never carries the meaning: SCAN_IMAGE_ONLY is shared
// by a scan that was read by OCR and a scan that was not.
import { getTranslations } from "next-intl/server";
import diff from "@/components/diff/DiffView.module.css";
import styles from "@/components/demo/Demo.module.css";

export const READ_CODES = new Set(["SCAN_IMAGE_ONLY", "OCR_LOW_CONFIDENCE", "OCR_UNAVAILABLE", "DOC_UNREADABLE"]);

export type ReadLike = {
  reason_code: string | null;
  variant: string | null;
  values: Record<string, string | number | undefined>;
};

export async function ReasonLine({ code, read, fallback }: { code: string; read?: ReadLike | null; fallback: string }) {
  const t = await getTranslations("demo");
  const to = await getTranslations("demo.ocr");
  const fromRead = read && read.variant && READ_CODES.has(code) ? read : null;
  const values = { max_pages: 50, ...(fromRead?.values ?? {}) } as Record<string, string | number>;
  const text = fromRead ? to(`why.${fromRead.variant}` as never, values as never) : fallback;
  return (
    <>
      {text}{" "}
      <span className={`${styles.mono} ${diff.muted}`} aria-label={t("case.reasonCode", { code })}>
        {code}
      </span>
    </>
  );
}
