// RB-02 validation queue (RB-01 overview via ?view=overview). Slice 1 lists the cases the gateway
// holds for the official's region with a link to their affidavit diff (RB-05); the risk-banded queue
// table arrives with M11 (P-10, P-12).
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/ui/PageHeader";
import styles from "@/components/ui/Page.module.css";
import { apiGet } from "@/lib/api";
import { requireRole } from "@/lib/session";
import { CaseList, type CaseRow } from "./CaseList";

type Props = { searchParams: Promise<{ view?: string }> };

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const t = await getTranslations("queue");
  const overview = (await searchParams).view === "overview";
  return {
    title: overview ? t("overviewTitle") : t("title"),
    description: overview ? t("overviewDescription") : t("description"),
  };
}

export default async function QueuePage({ searchParams }: Props) {
  const overview = (await searchParams).view === "overview";
  await requireRole("RB", overview ? "/rb-queue?view=overview" : "/rb-queue");
  const t = await getTranslations("queue");
  const portal = process.env.SATYA_PORTAL_ORIGIN ?? "https://portal.localhost";
  const path = overview ? "/rb-queue?view=overview" : "/rb-queue";
  const { items } = await apiGet<{ items: CaseRow[] }>("/v1/cases", path);
  return (
    <>
      <PageHeader title={overview ? t("overviewTitle") : t("title")}>
        <p className={styles.lede}>{t("intro")}</p>
      </PageHeader>
      {items.length > 0 ? (
        <CaseList items={items} />
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
