// Case view: documents with one of the six labels, source responses (Simulated source tag), manual tasks,
// the risk band and its reasons, and every finding with its evidence, decision bar and PDF viewer.
// Advisory only (guard rail 1): there is no approve or reject control.
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { CaseTabs } from "@/components/case/CaseTabs";
import { CaseReview } from "@/components/demo/CaseReview";
import styles from "@/components/demo/Demo.module.css";
import { RiskBand } from "@/components/demo/RiskBand";
import { SourceTag } from "@/components/ui/SourceTag";
import { StatusLabel } from "@/components/ui/StatusLabel";
import diff from "@/components/diff/DiffView.module.css";
import { SignatureBadge } from "@/components/signature/SignatureBadge";
import { PageHeader } from "@/components/ui/PageHeader";
import { ReadNotes } from "@/components/demo/ReadNotes";
import { ReasonLine } from "@/components/demo/ReasonLine";
import { caseVerification } from "@/lib/cases";
import { caseReview } from "@/lib/demo";
import { LABEL_ORDER } from "@/lib/labels";
import { requireRole } from "@/lib/session";
import { Note } from "@/components/ui/Note";

const cat = (...parts: string[]): string => parts.join("");

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const t = await getTranslations("demo");
  const { id } = await params;
  return { title: t("case.title", { case: id.slice(-4) }), description: t("case.description") };
}

export default async function CasePage({ params }: Props) {
  const { id } = await params;
  const base = `/case/${id}`;
  await requireRole("RB", base);
  const [review, verification] = await Promise.all([caseReview(id, base), caseVerification(id, base)]);
  const t = await getTranslations("demo");
  const td = await getTranslations("diff");
  const tv = await getTranslations("verification");
  return (
    <>
      <PageHeader title={t("case.heading")}>
        <p className={diff.caseLine}>
          {verification.documents.length > 0 ? t("case.line", { count: verification.documents.length, id: id.slice(-4) }) : null}
        </p>
        <Note>{td("advisory")}</Note>
        <CaseTabs caseId={id} current="overview" />
      </PageHeader>

      <section className={diff.section} aria-labelledby="band">
        <h2 id="band">{t("case.bandHeading")}</h2>
        <p>
          <RiskBand band={review.risk.band} /> <span>{t(`status.${review.status}`)}</span>
        </p>
        <p className={diff.note}>{t("case.bandNote")}</p>
        {review.risk.reasons.length > 0 ? (
          <ul className={styles.reasons}>
            {review.risk.reasons.map((r) => (
              <li key={r.flag_id}>
                {cat(r.rule_id, " (", r.aph_clause ?? t("flags.verify"), "): ", r.short_text)}
              </li>
            ))}
          </ul>
        ) : (
          <p>{t("case.noReasons")}</p>
        )}
      </section>

      <section className={diff.section} aria-labelledby="docs">
        <h2 id="docs">{t("case.docsHeading")}</h2>
        <ul className={styles.counts} aria-label={t("case.countsLabel")}>
          {LABEL_ORDER.map((label) => (
            <li key={label}>
              <StatusLabel label={label} count={review.label_counts[label]} />
            </li>
          ))}
        </ul>
        <div className={diff.tableWrap}>
          <table className={diff.table}>
            <caption>{t("case.docsCaption")}</caption>
            <thead>
              <tr>
                <th scope="col">{t("case.colDocument")}</th>
                <th scope="col">{t("case.colLabel")}</th>
                <th scope="col">{t("case.colIssuerSig")}</th>
                <th scope="col">{t("case.colUploaderSig")}</th>
                <th scope="col">{t("case.colSource")}</th>
                <th scope="col">{t("case.colHash")}</th>
              </tr>
            </thead>
            <tbody>
              {review.documents.map((d) => (
                <tr key={d.doc_id}>
                  <th scope="row">
                    {d.title}
                    <br />
                    <span className={diff.muted}>{d.slot}</span>
                  </th>
                  <td>
                    <StatusLabel label={d.label} />
                    {d.manual_task ? <p className={diff.note}>{t("case.manualTask")}</p> : null}
                    <ReadNotes read={d.read} />
                  </td>
                  <td>
                    <SignatureBadge sig={d.issuer_sig} />
                  </td>
                  <td>
                    <SignatureBadge sig={d.uploader_sig} />
                  </td>
                  <td>
                    {d.checks
                      .filter((c) => c.source)
                      .map((c) => (
                        <p key={`${c.reason_code}-${c.source?.adapter_id}`} className={diff.note}>
                          {cat(c.source?.name ?? "", ": ")}
                          <StatusLabel label={c.outcome} size="sm" />{" "}
                          <ReasonLine
                            code={c.reason_code}
                            fallback={tv.has(`reason.${c.reason_code}` as never) ? tv(`reason.${c.reason_code}` as never) : c.reason_code}
                          />
                          {c.response_sha256 ? <span className={styles.mono}> {c.response_sha256.slice(0, 12)}</span> : null}{" "}
                          {c.source?.mode === "mock" ? <SourceTag kind="simulated" /> : null}
                        </p>
                      ))}
                    <p className={diff.note}>
                      {t("case.chainSource")} <SourceTag kind="testAnchor" />
                    </p>
                  </td>
                  <td className={styles.mono}>{d.sha256.slice(0, 16)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {review.tasks.length > 0 ? (
          <>
            <h3>{t("case.tasksHeading")}</h3>
            <ul>
              {review.tasks.map((task) => (
                <li key={task.doc_id}>
                  {t("case.task", { title: task.title })}{" "}
                  <ReasonLine
                    code={task.reason}
                    read={review.documents.find((d) => d.doc_id === task.doc_id)?.read}
                    fallback={tv.has(`reason.${task.reason}` as never) ? tv(`reason.${task.reason}` as never) : task.reason}
                  />
                </li>
              ))}
            </ul>
          </>
        ) : null}
        <p className={diff.note}>{t("case.mockNote")}</p>
      </section>

      <section className={diff.section} aria-labelledby="flags">
        <h2 id="flags">{t("flags.heading")}</h2>
        <p className={diff.note}>{t("flags.intro", { count: review.flags.length, open: review.undisposed_flags })}</p>
        <CaseReview caseId={id} flags={review.flags} />
      </section>
    </>
  );
}
