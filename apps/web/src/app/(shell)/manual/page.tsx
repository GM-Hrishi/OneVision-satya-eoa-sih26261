// Manual checks (RB-09, UI spec §7.6): documents that need a person. Lists the open checks the overview reports
// (oldest first). There is no manual-task list or resolve endpoint on this build, so each row opens its case,
// where the decision (with a reason) is recorded. Advisory only: nothing here approves, rejects or clears.
import type { Metadata } from "next";
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { Numeral } from "@/components/k/Numeral";
import dk from "@/components/k/Doc.module.css";
import { overview } from "@/lib/demo";
import { requireRole } from "@/lib/session";

const AY = "2026-27";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("k.manual");
  return { title: t("title"), description: t("description") };
}

export default async function ManualPage() {
  await requireRole("RB", "/manual");
  const [t, to, data] = await Promise.all([getTranslations("k.manual"), getTranslations("overview"), overview("/manual", AY)]);
  const tasks = [...data.manual_tasks.top].sort((a, b) => b.age_days - a.age_days);
  const reason = (code: string) => (to.has(`reason.${code}` as never) ? to(`reason.${code}` as never) : t("unknownReason"));
  return (
    <>
      <header>
        <h1>{t("headline", { count: data.manual_tasks.open })}</h1>
      </header>
      <ul className={dk.numerals} aria-label={t("numeralsLabel")}>
        <li>
          <Numeral value={data.manual_tasks.open} caption={t("open")} tone="ink" />
        </li>
        <li>
          <Numeral value={data.documents.by_label.source_unavailable} caption={t("unavailable")} tone="ink" />
        </li>
        <li>
          <Numeral value={data.manual_tasks.open > 0 ? data.manual_tasks.oldest_age_days : 0} caption={t("oldest")} tone="ink" />
        </li>
      </ul>
      <section className={dk.section} aria-labelledby="manual-list">
        <h2 id="manual-list" className={dk.sectionTitle}>
          {t("tableHeading")}
        </h2>
        {tasks.length === 0 ? (
          <p>{t("empty")}</p>
        ) : (
          <div className={dk.scroll}>
            <table className={dk.table}>
              <thead>
                <tr>
                  <th scope="col" className="k-label">{t("colApplication")}</th>
                  <th scope="col" className="k-label">{t("colReason")}</th>
                  <th scope="col" className="k-label">{t("colAge")}</th>
                  <th scope="col" className="k-label">{t("colOpen")}</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={`${task.case_id}-${task.reason_key}`}>
                    <th scope="row" className="k-mono">
                      {task.application_id}
                    </th>
                    <td>{reason(task.reason_key)}</td>
                    <td>{t("age", { days: task.age_days })}</td>
                    <td>
                      <Link href={`/case/${task.case_id}#docs`} aria-label={t("openAria", { id: task.application_id })}>
                        {t("openCase")}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="k-label">{t("listNote")}</p>
      </section>
    </>
  );
}
