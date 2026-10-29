// Alerts panel: derived from stored data (certificate dates, High band cases, source tasks), each
// with a link to its case. Nothing is typed in by hand. Cards are ordered unread first, then by
// severity (High, Medium, Low), then newest first.
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { AlertCard } from "@/components/alerts/AlertCard";
import styles from "@/components/demo/Demo.module.css";
import diff from "@/components/diff/DiffView.module.css";
import { PageHeader } from "@/components/ui/PageHeader";
import { nowMs, rankAlerts, seenKeys } from "@/lib/alerts";
import { alerts } from "@/lib/demo";
import { requireRole } from "@/lib/session";
import { Note } from "@/components/ui/Note";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("demo");
  return { title: t("alerts.title"), description: t("alerts.description") };
}

export default async function AlertsPage() {
  await requireRole("RB", "/alerts");
  const { items } = await alerts("/alerts");
  const t = await getTranslations("demo");
  const ranked = rankAlerts(items, await seenKeys());
  const unread = ranked.filter((r) => r.unread);
  const earlier = ranked.filter((r) => !r.unread);
  const now = nowMs();
  const group = (id: string, heading: string, list: typeof ranked) =>
    list.length === 0 ? null : (
      <section aria-labelledby={id} className={diff.section}>
        <h2 id={id}>{heading}</h2>
        <ul className={styles.alertList}>
          {list.map(({ alert, unread: isUnread }) => (
            <li key={alert.alert_key}>
              <AlertCard alert={alert} unread={isUnread} nowMs={now} />
            </li>
          ))}
        </ul>
      </section>
    );
  return (
    <>
      <PageHeader title={t("alerts.heading")}>
        <Note>{t("alerts.intro")}</Note>
      </PageHeader>
      {items.length === 0 ? <p>{t("alerts.empty")}</p> : null}
      {group("alerts-unread", t("alerts.unreadHeading", { count: unread.length }), unread)}
      {group("alerts-earlier", t("alerts.earlierHeading", { count: earlier.length }), earlier)}
    </>
  );
}
