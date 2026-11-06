"use client";
// The case workbench (style K): pinned findings on the left, the document as white paper in the middle,
// limitation note and other documents on the right, then the proof ladder (server-rendered, passed as
// `ladder`) and the decision strip as the LAST block (emphasis rule 6). Selecting a finding moves the
// viewer to its page and region and points the decision strip at it. Advisory only: no approve or reject.
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useState, type ReactNode } from "react";
import { DecisionBar } from "@/components/demo/CaseReview";
import { PdfViewer, type ViewerTarget } from "@/components/demo/PdfViewer";
import { StatusLabel } from "@/components/ui/StatusLabel";
import type { FindingVM } from "@/lib/api/k-adapters/case";
import type { VerificationLabel } from "@satya/shared-types";
import { LimitationNote } from "./LimitationNote";
import { Numeral } from "./Numeral";
import { Paper } from "./Paper";
import { Pin } from "./Pin";
import { Untrusted } from "./Untrusted";
import styles from "./CaseWorkspace.module.css";

export interface CaseDoc {
  docId: string;
  title: string;
  label: VerificationLabel;
  manualTask: boolean;
}

export function CaseWorkspace({ caseId, findings, docs, ladder }: { caseId: string; findings: FindingVM[]; docs: CaseDoc[]; ladder: ReactNode }) {
  const t = useTranslations("demo");
  const tk = useTranslations("k");
  const [selectedId, setSelectedId] = useState<string | null>(findings[0]?.flag.flag_id ?? null);
  const selected = findings.find((f) => f.flag.flag_id === selectedId) ?? null;
  const flag = selected?.flag ?? null;
  const target: ViewerTarget | null =
    flag && flag.page && flag.doc_id
      ? { caseId, docId: flag.doc_id, page: flag.page, regions: flag.regions ?? [], label: `${flag.doc_title}, ${t("page", { page: flag.page })}`, pin: selected?.n }
      : null;
  const viewerText = {
    title: t("viewer.title"),
    empty: t("viewer.empty"),
    loading: t("viewer.loading"),
    failed: t("viewer.failed"),
    page: t("viewer.page", { page: "{page}", pages: "{pages}" }),
    prev: t("viewer.prev"),
    next: t("viewer.next"),
  };
  return (
    <>
      <div className={styles.grid}>
        <section id="flags" className={styles.col} aria-labelledby="flags-h">
          <h2 id="flags-h">{tk("case.findingsHeading")}</h2>
          {findings.length === 0 ? (
            <p className={styles.empty}>{tk("case.findingsEmpty")}</p>
          ) : (
            <ol className={styles.findings}>
              {findings.map((f) => (
                <li key={f.flag.flag_id} className={styles.finding} data-selected={f.flag.flag_id === selectedId}>
                  <div className={styles.head}>
                    <Pin n={f.n} />
                    <span className={styles.rule}>{f.flag.rule_id}</span>
                    <span className="k-label">{t(`severity.${f.flag.severity}`)}</span>
                    <StatusLabel label={f.flag.label} size="sm" />
                  </div>
                  {f.values ? (
                    <div className={styles.pair}>
                      <Numeral
                        tone="red"
                        value={f.values.left}
                        caption={
                          <>
                            {f.values.unit ?? ""} <span className={styles.pairSource}>{f.values.leftSource}</span>
                          </>
                        }
                      />
                      <Numeral tone="ink" value={f.values.right} caption={<span className={styles.pairSource}>{f.values.rightSource}</span>} />
                    </div>
                  ) : null}
                  <p className={styles.why}>{f.why}</p>
                  {f.aiReader ? (
                    <div className={styles.aiBlock}>
                      <p style={{ margin: 0 }}>{tk("aiReader.line")}</p>
                      <p style={{ margin: 0 }}>{tk("aiReader.where", { page: f.flag.page ?? 0 })}</p>
                      <span className="k-label">{tk("aiReader.snippet")}</span>
                      <Untrusted value={f.flag.extracted_value} className={styles.snippet} />
                    </div>
                  ) : null}
                  <p className={styles.meta}>
                    {f.flag.aph_clause ? t("flags.clause", { clause: f.flag.aph_clause }) : t("flags.verify")}
                    {" · "}
                    {f.flag.disposition ? t("flags.disposed", { action: t(`action.${f.flag.disposition.action}`) }) : t("flags.undisposed")}
                  </p>
                  {f.flag.preliminary_indicator || f.heuristic ? <p className={styles.meta}>{t("flags.prelim")}</p> : null}
                  <button
                    type="button"
                    className={styles.showButton}
                    aria-current={f.flag.flag_id === selectedId ? "true" : undefined}
                    aria-label={tk("case.selectFinding", { n: f.n })}
                    onClick={() => setSelectedId(f.flag.flag_id)}
                  >
                    {t("flags.show")}
                  </button>
                </li>
              ))}
            </ol>
          )}
        </section>

        <section className={styles.col} aria-labelledby="k-doc">
          <h2 id="k-doc">{tk("case.documentHeading")}</h2>
          <Paper>
            <PdfViewer key={target ? `${target.docId}-${target.page}-${target.pin}` : "none"} target={target} text={viewerText} />
          </Paper>
        </section>

        <aside className={styles.col} aria-labelledby="k-side">
          <LimitationNote text={selected?.limitation} />
          <h2 id="k-side">{tk("case.sideHeading")}</h2>
          {docs.length === 0 ? (
            <p className={styles.empty}>{tk("case.noDocuments")}</p>
          ) : (
            <ul className={styles.docList}>
              {docs.map((d) => (
                <li key={d.docId} className={styles.docItem}>
                  <span className={styles.docTitle}>{d.title}</span>
                  <StatusLabel label={d.label} />
                  {d.manualTask ? <span className="k-label">{t("case.manualTask")}</span> : null}
                </li>
              ))}
            </ul>
          )}
          <Link href={`/case/${caseId}/verification`}>{t("case.docsHeading")}</Link>
        </aside>
      </div>

      {ladder}

      {flag ? (
        <section className={styles.decision} aria-labelledby="k-decision">
          <h2 id="k-decision" className="k-label">
            {tk("case.decisionHeading")}
          </h2>
          <p className={styles.meta}>{tk("case.pinLine", { n: selected?.n ?? 0, rule: flag.rule_id })}</p>
          <DecisionBar key={flag.flag_id} caseId={caseId} flag={flag} />
        </section>
      ) : null}
    </>
  );
}
