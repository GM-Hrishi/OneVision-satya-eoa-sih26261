"use client";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useActionState } from "react";
import { pickDocument, uploadDocument, type FormState } from "@/app/actions/demo";
import styles from "./Demo.module.css";

const INITIAL: FormState = { ok: false, code: null };

function Result({ state, caseId }: { state: FormState; caseId: string }) {
  const t = useTranslations("demo");
  if (state.code) {
    return (
      <p role="alert" className={styles.error}>
        {t.has(`error.${state.code}` as never) ? t(`error.${state.code}` as never) : t("error.INTERNAL_ERROR")}
      </p>
    );
  }
  if (state.ok) {
    return (
      <p role="status" className={styles.recorded}>
        {t("upload.done")} <Link href={`/case/${caseId}`}>{t("upload.viewCase")}</Link>
      </p>
    );
  }
  return null;
}

export function UploadForms({ caseId, sources }: { caseId: string; sources: { id: string; name: string }[] }) {
  const t = useTranslations("demo");
  const [up, upAction, upPending] = useActionState(uploadDocument, INITIAL);
  const [pick, pickAction, pickPending] = useActionState(pickDocument, INITIAL);
  return (
    <>
      <section aria-labelledby="up-file">
        <h2 id="up-file">{t("upload.fileHeading")}</h2>
        <form action={upAction} className={styles.formGrid}>
          <input type="hidden" name="case_id" value={caseId} />
          <label>
            <span>{t("upload.slot")}</span>
            <select name="slot" className={styles.field} required>
              <option value="affidavit">{t("upload.slotAffidavit")}</option>
              <option value="accounts">{t("upload.slotAccounts")}</option>
            </select>
          </label>
          <label>
            <span>{t("upload.file")}</span>
            <input type="file" name="file" accept="application/pdf,.pdf" className={styles.field} required />
          </label>
          <p>{t("upload.rules")}</p>
          <Result state={up} caseId={caseId} />
          <div>
            <button type="submit" className={styles.button} disabled={upPending}>
              {upPending ? t("upload.checking") : t("upload.submit")}
            </button>
          </div>
        </form>
      </section>
      <section aria-labelledby="up-pick">
        <h2 id="up-pick">{t("upload.pickHeading")}</h2>
        <form action={pickAction} className={styles.formGrid}>
          <input type="hidden" name="case_id" value={caseId} />
          <label>
            <span>{t("upload.slot")}</span>
            <select name="slot" className={styles.field} required>
              <option value="affidavit">{t("upload.slotAffidavit")}</option>
              <option value="accounts">{t("upload.slotAccounts")}</option>
            </select>
          </label>
          <label>
            <span>{t("upload.pickFrom")}</span>
            <select name="source_case_id" className={styles.field} required>
              {sources.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <Result state={pick} caseId={caseId} />
          <div>
            <button type="submit" className={styles.button} disabled={pickPending}>
              {pickPending ? t("upload.checking") : t("upload.pickSubmit")}
            </button>
          </div>
        </form>
      </section>
    </>
  );
}
