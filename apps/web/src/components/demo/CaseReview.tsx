"use client";
// Flags of a case with evidence, a fixed-template "why" sentence, the decision bar and the PDF
// viewer. Choosing "Show in document" opens the PDF at the flag's page and outlines its region.
// Advisory only: the five dispositions record an observation; nothing is approved or rejected.
import { useTranslations } from "next-intl";
import { useActionState, useState } from "react";
import { recordDisposition, type FormState } from "@/app/actions/demo";
import { ACTIONS, type ReviewFlag } from "@/lib/demo-types";
import styles from "./Demo.module.css";
import { PdfViewer, type ViewerTarget } from "./PdfViewer";

const INITIAL: FormState = { ok: false, code: null };

function show(value: unknown): string {
  if (value === null || value === undefined) return "";
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}

function DecisionBar({ caseId, flag }: { caseId: string; flag: ReviewFlag }) {
  const t = useTranslations("demo");
  const [state, action, pending] = useActionState(recordDisposition, INITIAL);
  const done = flag.disposition;
  return (
    <form action={action} className={styles.decision} aria-label={t("decision.heading")}>
      <input type="hidden" name="case_id" value={caseId} />
      <input type="hidden" name="flag_id" value={flag.flag_id} />
      {done ? (
        <p className={styles.recorded} role="status">
          {t("decision.recorded", { action: t(`action.${done.action}`), no: done.ledger_no })}
          <br />
          {done.reason}
        </p>
      ) : null}
      <fieldset>
        <legend>{done ? t("decision.again") : t("decision.heading")}</legend>
        {ACTIONS.map((a) => (
          <label key={a} className={styles.radio}>
            <input type="radio" name="action" value={a} required />
            <span>{t(`action.${a}`)}</span>
          </label>
        ))}
      </fieldset>
      <label>
        <span>{t("decision.reason")}</span>
        <textarea name="reason" className={styles.textarea} required minLength={10} maxLength={4000} aria-describedby={`why-${flag.flag_id}`} />
      </label>
      <p id={`why-${flag.flag_id}`}>{t("decision.hint")}</p>
      {state.code ? (
        <p role="alert" className={styles.error}>
          {t.has(`error.${state.code}` as never) ? t(`error.${state.code}` as never) : t("error.INTERNAL_ERROR")}
        </p>
      ) : null}
      {state.ok ? (
        <p role="status" className={styles.recorded}>
          {t("decision.saved")}
        </p>
      ) : null}
      <button type="submit" className={styles.button} disabled={pending}>
        {pending ? t("decision.recording") : t("decision.record")}
      </button>
    </form>
  );
}

export function CaseReview({ caseId, flags }: { caseId: string; flags: ReviewFlag[] }) {
  const t = useTranslations("demo");
  const [selected, setSelected] = useState<string | null>(flags[0]?.flag_id ?? null);
  const flag = flags.find((f) => f.flag_id === selected) ?? null;
  const target: ViewerTarget | null =
    flag && flag.page && flag.doc_id
      ? { caseId, docId: flag.doc_id, page: flag.page, regions: flag.regions ?? [], label: `${flag.doc_title}, ${t("page", { page: flag.page })}` }
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
  if (flags.length === 0) return <p>{t("flags.none")}</p>;
  return (
    <div className={styles.review}>
      <ol style={{ listStyle: "none", padding: 0, margin: 0 }} aria-label={t("flags.heading")}>
        {flags.map((f) => (
          <li key={f.flag_id} className={styles.flagItem} data-selected={f.flag_id === selected}>
            <div className={styles.flagHead}>
              <strong>{f.rule_id}</strong>
              <span>{t(`severity.${f.severity}`)}</span>
              <span>{f.aph_clause ? t("flags.clause", { clause: f.aph_clause }) : t("flags.verify")}</span>
            </div>
            <p className={styles.why}>{f.why}</p>
            <dl className={styles.evidence}>
              <dt>{t("flags.extracted")}</dt>
              <dd>{show(f.extracted_value) || t("flags.nothing")} {f.value_unit ?? ""}</dd>
              <dt>{t("flags.expected")}</dt>
              <dd>{show(f.expected_value) || t("flags.nothing")} {f.value_unit ?? ""}</dd>
              <dt>{t("flags.region")}</dt>
              <dd>{[f.doc_title, ", ", f.page ? t("page", { page: f.page }) : t("flags.noPage")].join("")}</dd>
            </dl>
            <p>
              <button type="button" className={styles.linkButton} onClick={() => setSelected(f.flag_id)} aria-pressed={f.flag_id === selected}>
                {t("flags.show")}
              </button>
              {" · "}
              <span>{f.disposition ? t("flags.disposed", { action: t(`action.${f.disposition.action}`) }) : t("flags.undisposed")}</span>
            </p>
            <p className={styles.mono}>{t("flags.prelim")}</p>
            {f.flag_id === selected ? <DecisionBar caseId={caseId} flag={f} /> : null}
          </li>
        ))}
      </ol>
      <div className={styles.viewerCol}>
        <PdfViewer key={target ? `${target.docId}-${target.page}` : "none"} target={target} text={viewerText} />
      </div>
    </div>
  );
}
