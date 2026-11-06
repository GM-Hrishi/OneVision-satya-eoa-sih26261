// View-models for the document evidence page. Pure and tested. Dates and values come from the API only.
import type { AffidavitChronology, CaseVerificationDocument } from "@satya/shared-types";

export interface CompareRow {
  key: string;
  field: string;
  submitted: string;
  record: string;
  sourceName: string | null;
  simulated: boolean;
}

const show = (v: string | number | boolean | null): string => (v === null ? "" : String(v));

/** Every field the checks compared with a source record: what was submitted, what the record says. */
export function compareRows(doc: Pick<CaseVerificationDocument, "checks">): CompareRow[] {
  const rows: CompareRow[] = [];
  for (const [i, check] of (doc.checks ?? []).entries()) {
    for (const [j, d] of (check.field_diff ?? []).entries()) {
      rows.push({
        key: `${i}-${j}-${d.field}`,
        field: d.field,
        submitted: show(d.submitted),
        record: show(d.source),
        sourceName: check.source?.name ?? null,
        simulated: check.source?.mode === "mock",
      });
    }
  }
  return rows;
}

export const CHRONO_KEYS = ["application_date", "stamp_date", "notary_date", "dsc_date", "upload_date", "notary_expiry"] as const;
export type ChronoKey = (typeof CHRONO_KEYS)[number];

export interface ChronoItem {
  key: ChronoKey;
  date: string;
}

/** Dates in the order the API defines them (application, stamp, notarisation, signing, upload). Missing dates are left out. */
export function chronologyItems(c: AffidavitChronology | null | undefined): ChronoItem[] {
  if (!c) return [];
  return CHRONO_KEYS.flatMap((key) => {
    const value = c[key as keyof AffidavitChronology];
    return typeof value === "string" && value.length > 0 ? [{ key, date: value }] : [];
  });
}
