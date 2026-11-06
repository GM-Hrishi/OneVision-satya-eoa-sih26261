// RB-02 validation queue. Lists the cases the gateway holds for the official's region, risk band
// groups first. Overview links land here with band, label or status already set.
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { Numeral } from "@/components/k/Numeral";
import { QueueViews } from "@/components/k/QueueViews";
import { RiskBand } from "@/components/demo/RiskBand";
import { buildTimeline } from "@/lib/api/k-adapters/timeline";
import { BANDS } from "@/lib/demo-types";
import styles from "@/components/ui/Page.module.css";
import ql from "@/components/k/QueueTimeline.module.css";
import { queue } from "@/lib/demo";
import { requireRole } from "@/lib/session";
import { applyFilters, CaseList, parseQuery } from "./CaseList";

type Props = { searchParams: Promise<Record<string, string | undefined>> };

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("queue");
  return { title: t("title"), description: t("description") };
}

export default async function QueuePage({ searchParams }: Props) {
  const params = await searchParams;
  await requireRole("RB", "/rb-queue");
  const t = await getTranslations("queue");
  const tk = await getTranslations("k.queue");
  const portal = process.env.SATYA_PORTAL_ORIGIN ?? "https://portal.localhost";
  const query = parseQuery(params);
  const { items } = await queue("/rb-queue", query.sort ?? undefined);
  const asOf = new Date().toISOString();
  return (
    <>
      <header>
        <h1>{tk("headline", { count: items.length })}</h1>
        <p className={styles.lede}>{t("intro")}</p>
      </header>
      {items.length > 0 ? (
        <ul className={ql.groups} aria-label={tk("groupsLabel")}>
          {BANDS.map((b) => (
            <li key={b}>
              <Numeral value={items.filter((r) => r.risk_band === b).length} tone={b === "high" ? "red" : "ink"} caption={<RiskBand band={b} />} />
            </li>
          ))}
        </ul>
      ) : null}
      {items.length > 0 ? (
        <QueueViews
          timeline={buildTimeline(applyFilters(items, query), asOf)}
          list={<CaseList items={applyFilters(items, query)} total={items.length} query={query} />}
        />
      ) : (
        <section className={styles.empty} aria-labelledby="queue-empty">
          <p id="queue-empty" className={styles.emptyTitle}>
            {t("emptyTitle")}
          </p>
          <p>{t("emptyBody")}</p>
          <p>
            <a href={portal}>{t("emptyLink")}</a>
          </p>
        </section>
      )}
    </>
  );
}
