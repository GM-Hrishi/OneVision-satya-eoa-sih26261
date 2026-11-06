// Rules (read only, UI spec §7.7). The full rule list has no endpoint on this build, so this page says so and lists the
// rules that raised a finding on files in the queue, each linking to its detail. Advisory only.
import type { Metadata } from "next";
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import dk from "@/components/k/Doc.module.css";
import { seenRules } from "@/lib/api/k-adapters/rules";
import { queue } from "@/lib/demo";
import { requireRole } from "@/lib/session";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("k.rules");
  return { title: t("title"), description: t("description") };
}

export default async function RulesPage() {
  await requireRole("RB", "/rules");
  const [t, { items }] = await Promise.all([getTranslations("k.rules"), queue("/rules")]);
  const rules = seenRules(items);
  return (
    <>
      <header>
        <h1>{t("headline")}</h1>
        <p>{t("listUnavailable")}</p>
      </header>
      <section className={dk.section} aria-labelledby="rules-seen">
        <h2 id="rules-seen" className={dk.sectionTitle}>
          {t("seenHeading")}
        </h2>
        {rules.length === 0 ? (
          <p>{t("seenNone")}</p>
        ) : (
          <div className={dk.scroll}>
            <table className={dk.table}>
              <thead>
                <tr>
                  <th scope="col" className="k-label">{t("colRule")}</th>
                  <th scope="col" className="k-label">{t("colClause")}</th>
                  <th scope="col" className="k-label">{t("colStatement")}</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((r) => (
                  <tr key={r.ruleId}>
                    <th scope="row">
                      <Link className="k-mono" href={`/rules/${encodeURIComponent(r.ruleId)}`} aria-label={t("open", { id: r.ruleId })}>
                        {r.ruleId}
                      </Link>
                    </th>
                    <td>{r.clause ?? t("clauseUnconfirmed")}</td>
                    <td>{r.sentence}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
