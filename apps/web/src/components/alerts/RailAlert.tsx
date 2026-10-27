// The rail notification card: the most important unread alert, in the same card style as the
// Alerts page. Renders nothing for roles without alerts, when everything is read, or when the API
// does not answer (the rest of the page must never wait on or break because of this card).
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { nowMs, rankAlerts, seenKeys } from "@/lib/alerts";
import { alertsQuiet } from "@/lib/demo";
import { AlertCard } from "./AlertCard";
import styles from "./RailAlert.module.css";

export async function RailAlert() {
  const data = await alertsQuiet();
  if (!data) return null;
  const unread = rankAlerts(data.items, await seenKeys()).filter((r) => r.unread);
  const top = unread[0];
  if (!top) return null;
  const t = await getTranslations("demo");
  return (
    <section className={styles.rail} aria-label={t("alerts.railLabel")}>
      <AlertCard alert={top.alert} unread compact nowMs={nowMs()} />
      <Link href="/alerts" className={styles.all}>
        {t("alerts.viewAll", { count: unread.length })}
      </Link>
    </section>
  );
}
