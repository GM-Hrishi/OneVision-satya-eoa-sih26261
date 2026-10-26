// RB-02 validation queue (RB-01 overview via ?view=overview). Slice 0: the real empty state only;
// the queue table arrives with M11 (P-10, P-12).
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/ui/PageHeader";
import styles from "@/components/ui/Page.module.css";
import { requireRole } from "@/lib/session";

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
  return (
    <>
      <PageHeader title={overview ? t("overviewTitle") : t("title")}>
        <p className={styles.lede}>{t("intro")}</p>
      </PageHeader>
      <section className={styles.empty} aria-labelledby="queue-empty">
        <p id="queue-empty" className={styles.emptyTitle}>
          {t("emptyTitle")}
        </p>
        <p>{t("emptyBody")}</p>
        <p>
          <a href={portal}>{t("emptyLink")}</a>
        </p>
      </section>
    </>
  );
}
