"use client";
// The decision bar for one finding (style K segmented radios). Advisory only: the five dispositions record an
// observation with a reason; nothing is approved or rejected. The case page (components/k/CaseWorkspace) renders it.
import { useTranslations } from "next-intl";
import { useActionState } from "react";
import { useMotion } from "@/components/ui/useMotion";
import { recordDisposition, type FormState } from "@/app/actions/demo";
import { ACTIONS, type ReviewFlag } from "@/lib/demo-types";
import styles from "./Demo.module.css";

const INITIAL: FormState = { ok: false, code: null };

export function DecisionBar({ caseId, flag }: { caseId: string; flag: ReviewFlag }) {
  const t = useTranslations("demo");
  const [state, action, pending] = useActionState(recordDisposition, INITIAL);
  const done = flag.disposition;
  const { cls } = useMotion();
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
        <p role="status" className={`${styles.recorded} ${cls("stamp")}`}>
          {t("decision.saved")}
        </p>
      ) : null}
      <button type="submit" className={styles.button} disabled={pending}>
        {pending ? t("decision.recording") : t("decision.record")}
      </button>
    </form>
  );
}
