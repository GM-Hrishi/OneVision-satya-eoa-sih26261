// Document evidence (style K): one document's proof. A one-sentence headline, what was submitted against what the
// issuer record says (Simulated source tag), what each check found, the stamp-paper and signing dates, what this
// does not prove, and all documents of the case. Advisory only; nothing here approves, rejects or clears.
import type { AffidavitChronology, AffidavitDiff } from "@satya/shared-types";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getLocale, getTranslations } from "next-intl/server";
import { LimitationNote } from "@/components/k/LimitationNote";
import dk from "@/components/k/Doc.module.css";
import { SignatureBadge } from "@/components/signature/SignatureBadge";
import { SourceTag } from "@/components/ui/SourceTag";
import { StatusLabel } from "@/components/ui/StatusLabel";
import { ReasonLine } from "@/components/demo/ReasonLine";
import { apiGetOptional } from "@/lib/api";
import { chronologyItems, compareRows } from "@/lib/api/k-adapters/document";
import { limitationText, whyText } from "@/lib/api/k-adapters/pending-fields";
import { caseVerification } from "@/lib/cases";
import { caseReview } from "@/lib/demo";
import { requireRole } from "@/lib/session";

const DOC_ID = /^doc_[0-9A-HJKMNP-TV-Z]{26}$/;
type Props = { params: Promise<{ id: string; docId: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const t = await getTranslations("k.doc");
  const { docId } = await params;
  return { title: t("title", { title: docId.slice(-4) }), description: t("description") };
}

export default async function DocumentEvidencePage({ params }: Props) {
  const { id, docId } = await params;
  if (!DOC_ID.test(docId)) notFound();
  const base = `/case/${id}/documents/${docId}`;
  await requireRole("RB", base);
  const [review, verification] = await Promise.all([caseReview(id, base), caseVerification(id, base)]);
  const doc = review.documents.find((d) => d.doc_id === docId);
  const vdoc = verification.documents.find((d) => d.doc_id === docId);
  if (!doc) notFound();
  const [t, tv, tl, locale] = await Promise.all([getTranslations("k.doc"), getTranslations("verification"), getTranslations("k.ladder"), getLocale()]);
  const flags = review.flags.filter((f) => f.doc_id === docId);
  const first = flags[0];
  const headline = first ? whyText(first) : tl(`verdict.${doc.label}`, { title: doc.title });
  const rows = vdoc ? compareRows(vdoc) : [];
  const diff = await apiGetOptional<AffidavitDiff>(`/v1/cases/${id}/affidavit-diff`, base);
  const chrono: AffidavitChronology | null = diff.status === "ok" && diff.data.doc_id === docId ? diff.data.chronology : null;
  const dates = chronologyItems(chrono);
  const fmt = new Intl.DateTimeFormat(locale === "hi" ? "hi-IN" : "en-IN", { timeZone: "Asia/Kolkata", dateStyle: "long" });
  const reason = (code: string) => (tv.has(`reason.${code}` as never) ? tv(`reason.${code}` as never) : code);
  return (
    <>
      <header>
        <h1>{headline}</h1>
        <p className={dk.status}>
          <StatusLabel label={doc.label} /> <span className="k-mono">{doc.title}</span>
        </p>
        <p>
          <Link href={`/case/${id}`}>{t("backToCase")}</Link>
        </p>
      </header>

      <section className={dk.section} aria-labelledby="doc-compare">
        <h2 id="doc-compare" className={dk.sectionTitle}>
          {t("compareHeading")}
        </h2>
        {rows.length === 0 ? (
          <p>{t("compareNone")}</p>
        ) : (
          <div className={dk.scroll}>
            <table className={dk.table}>
              <thead>
                <tr>
                  <th scope="col" className="k-label">{t("colField")}</th>
                  <th scope="col" className="k-label">{t("colSubmitted")}</th>
                  <th scope="col" className="k-label">{t("colRecord")}</th>
                  <th scope="col" className="k-label">{t("colSource")}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.key}>
                    <th scope="row">{r.field}</th>
                    <td className={dk.mono}>{r.submitted}</td>
                    <td className={dk.mono}>{r.record}</td>
                    <td>
                      {r.sourceName} {r.simulated ? <SourceTag kind="simulated" /> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className={dk.section} aria-labelledby="doc-checks">
        <h2 id="doc-checks" className={dk.sectionTitle}>
          {t("checksHeading")}
        </h2>
        <div className={dk.scroll}>
          <table className={dk.table}>
            <thead>
              <tr>
                <th scope="col" className="k-label">{t("colCheck")}</th>
                <th scope="col" className="k-label">{t("colOutcome")}</th>
                <th scope="col" className="k-label">{t("colSource")}</th>
              </tr>
            </thead>
            <tbody>
              {doc.checks.map((c, i) => (
                <tr key={`${c.kind}-${i}`}>
                  <th scope="row">{tv.has(`kind.${c.kind}` as never) ? tv(`kind.${c.kind}` as never) : c.kind}</th>
                  <td>
                    <StatusLabel label={c.outcome} size="sm" /> <ReasonLine code={c.reason_code} fallback={reason(c.reason_code)} />
                  </td>
                  <td>
                    {c.source?.name ?? ""} {c.source?.mode === "mock" ? <SourceTag kind="simulated" /> : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>
          <SignatureBadge sig={doc.issuer_sig} /> <SignatureBadge sig={doc.uploader_sig} />
        </p>
      </section>

      <section className={dk.section} aria-labelledby="doc-chrono">
        <h2 id="doc-chrono" className={dk.sectionTitle}>
          {t("chronoHeading")}
        </h2>
        {dates.length === 0 ? (
          <p>{t("chronoNone")}</p>
        ) : (
          <>
            <ol className={dk.timeline}>
              {dates.map((d) => (
                <li key={d.key}>
                  <span className="k-label">{t(`date.${d.key}`)}</span>
                  <time className={dk.date} dateTime={d.date}>
                    {fmt.format(new Date(d.date))}
                  </time>
                </li>
              ))}
            </ol>
            {chrono?.order_ok === null || chrono?.order_ok === undefined ? null : <p>{chrono.order_ok ? t("chronoOrderOk") : t("chronoOrderBad")}</p>}
          </>
        )}
      </section>

      {first ? <LimitationNote text={limitationText(first)} /> : null}

      <section className={dk.section} aria-labelledby="doc-all">
        <h2 id="doc-all" className={dk.sectionTitle}>
          {t("allHeading")}
        </h2>
        <div className={dk.scroll}>
          <table className={dk.table}>
            <thead>
              <tr>
                <th scope="col" className="k-label">{t("colDocument")}</th>
                <th scope="col" className="k-label">{t("colStatus")}</th>
                <th scope="col" className="k-label">{t("colWhy")}</th>
                <th scope="col" className="k-label">{t("colSource")}</th>
              </tr>
            </thead>
            <tbody>
              {review.documents.map((d) => {
                const f = review.flags.find((x) => x.doc_id === d.doc_id);
                const src = d.checks.find((c) => c.source)?.source;
                return (
                  <tr key={d.doc_id}>
                    <th scope="row" className={d.doc_id === docId ? dk.current : undefined}>
                      {d.doc_id === docId ? (
                        <span aria-current="page">{d.title}</span>
                      ) : (
                        <Link href={`/case/${id}/documents/${d.doc_id}`} aria-label={t("open", { title: d.title })}>
                          {d.title}
                        </Link>
                      )}
                    </th>
                    <td>
                      <StatusLabel label={d.label} size="sm" />
                    </td>
                    <td>{f ? whyText(f) : t("noFindings")}</td>
                    <td>
                      {src?.name ?? ""} {src?.mode === "mock" ? <SourceTag kind="simulated" /> : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
