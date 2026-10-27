// Alerts panel: derived from stored data (certificate dates, High band cases, source tasks), each
// with a link to its case. Nothing is typed in by hand.
import type { Metadata } from "next";
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import styles from "@/components/demo/Demo.module.css";
import diff from "@/components/diff/DiffView.module.css";
import { PageHeader } from "@/components/ui/PageHeader";
import { alerts } from "@/lib/demo";
import { requireRole } from "@/lib/session";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("demo");
  return { title: t("alerts.title"), description: t("alerts.description") };
}

export default async function AlertsPage() {
  await requireRole("RB", "/alerts");
  const { items } = await alerts("/alerts");
  const t = await getTranslations("demo");
  return (
    <>
      <PageHeader title={t("alerts.heading")}>
        <p className={diff.advisory}>{t("alerts.intro")}</p>
      </PageHeader>
      {items.length === 0 ? (
        <p>{t("alerts.empty")}</p>
      ) : (
        <ul className={styles.alertList}>
          {items.map((a, i) => (
            <li key={`${a.case_id}-${a.subtype}-${i}`}>
              <strong>{t(`alerts.type.${a.type}` as never)}</strong> · <span className={diff.mono}>{a.application_id}</span>
              <p>{a.text}</p>
              <Link href={`/case/${a.case_id}`}>{t("alerts.open")}</Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
