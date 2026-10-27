// RB-02 validation queue. Lists the cases the gateway holds for the official's region, risk band
// groups first. Overview links land here with band, label or status already set.
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/ui/PageHeader";
import styles from "@/components/ui/Page.module.css";
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
  const portal = process.env.SATYA_PORTAL_ORIGIN ?? "https://portal.localhost";
  const query = parseQuery(params);
  const { items } = await queue("/rb-queue", query.sort ?? undefined);
  return (
    <>
      <PageHeader title={t("title")}>
        <p className={styles.lede}>{t("intro")}</p>
      </PageHeader>
      {items.length > 0 ? (
        <CaseList items={applyFilters(items, query)} total={items.length} query={query} />
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
