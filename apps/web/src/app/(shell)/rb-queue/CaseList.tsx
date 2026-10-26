// Interim case list for the validation queue: the cases the gateway holds for this official's region,
// each linking to its RB-05 affidavit diff. The risk-banded queue (RB-02) arrives with M11 (P-10, P-12).
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import styles from "@/components/diff/DiffView.module.css";

export interface CaseRow {
  case_id: string;
  application_id: string;
  region: string;
  ay: string;
  route: string;
  stage: string;
  institution_name: string | null;
  open_flags: number | null;
}

export async function CaseList({ items }: { items: CaseRow[] }) {
  const t = await getTranslations("queue");
  const td = await getTranslations("diff");
  return (
    <section className={styles.section} aria-labelledby="case-list">
      <h2 id="case-list">{t("listHeading")}</h2>
      <p className={styles.note}>{t("listIntro")}</p>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th scope="col">{t("colApplication")}</th>
              <th scope="col">{t("colInstitution")}</th>
              <th scope="col">{t("colRegion")}</th>
              <th scope="col">{t("colAy")}</th>
              <th scope="col">{t("colRoute")}</th>
              <th scope="col">{t("colFindings")}</th>
              <th scope="col">{t("colOpen")}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.case_id}>
                <td className={styles.mono}>{c.application_id}</td>
                <td>{c.institution_name ?? td("none")}</td>
                <td>{c.region}</td>
                <td>{c.ay}</td>
                <td>
                  {td(`route.${c.route}`)} · {td(`stage.${c.stage}`)}
                </td>
                <td className={styles.num}>
                  {c.open_flags === null ? t("findingsUnavailable") : t("findings", { count: c.open_flags })}
                </td>
                <td>
                  <Link href={`/case/${c.case_id}/affidavit`} aria-label={t("openAria", { aid: c.application_id })}>
                    {t("openDiff")}
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
