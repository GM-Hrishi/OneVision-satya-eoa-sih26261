// AlertCard (v0.8): whole-card tint, full 1px border, 6px radius, no side stripe. Grid of icon,
// content and action. Severity is a word and an icon as well as a tint (never colour alone).
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { Icon, type IconName } from "@/components/ui/Icon";
import { SourceTag } from "@/components/ui/SourceTag";
import { StatusLabel } from "@/components/ui/StatusLabel";
import { ago, TONE } from "@/lib/alerts";
import type { AlertItem } from "@/lib/demo-types";
import styles from "./AlertCard.module.css";

const ICON: Record<"high" | "med" | "low", IconName> = { high: "alert-triangle", med: "alert-circle", low: "info-circle" };

export async function AlertCard({ alert, unread, compact = false, nowMs }: { alert: AlertItem; unread: boolean; compact?: boolean; nowMs: number }) {
  const t = await getTranslations("demo");
  const tone = TONE[alert.severity];
  const age = ago(alert.created_at, nowMs);
  const when = age.unit === "now" ? t("alerts.ago.now") : t(`alerts.ago.${age.unit}`, { n: age.n });
  const href =
    `/alerts/open?key=${alert.alert_key}&case=${alert.case_id}` + (alert.flag_id ? `&flag=${alert.flag_id}` : "");
  const action = alert.flag_id ? t("alerts.openFlag") : t("alerts.openDocument");
  return (
    <article className={styles.card} data-tone={tone} data-unread={unread ? "true" : undefined} data-compact={compact ? "true" : undefined}>
      <span className={styles.icon}>
        <Icon name={ICON[tone]} size={compact ? 16 : 18} />
      </span>
      <div className={styles.body}>
        <p className={styles.first}>
          <span className={styles.severity}>{t(`alerts.severity.${tone}`)}</span>
          {" · "}
          {t(`alerts.type.${alert.type}` as never)}
          {" · "}
          <time dateTime={alert.created_at}>{when}</time>
          {unread ? ` · ${t("alerts.unread")}` : ""}
        </p>
        <p className={styles.what}>{alert.text}</p>
        <p className={styles.meta}>
          <span className={styles.app}>{alert.application_id}</span>
          {alert.aph_clause ? <span className={styles.clause}>{t("flags.clause", { clause: alert.aph_clause })}</span> : null}
          {alert.label ? <StatusLabel label={alert.label} size="sm" /> : null}
          {alert.source ? <SourceTag kind="simulated" /> : null}
        </p>
        {alert.type === "suspected_anomaly" ? <p className={styles.prelim}>{t("flags.prelim")}</p> : null}
      </div>
      <Link className={styles.action} href={href} prefetch={false} aria-label={t("alerts.actionAria", { action, aid: alert.application_id })}>
        {action}
      </Link>
    </article>
  );
}
