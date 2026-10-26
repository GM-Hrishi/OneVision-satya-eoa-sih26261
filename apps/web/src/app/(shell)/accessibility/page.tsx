// SH-07 / GIGW accessibility statement.
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/ui/PageHeader";
import styles from "@/components/ui/Page.module.css";
import { pageMetadata } from "@/lib/page";

export const generateMetadata = (): Promise<Metadata> => pageMetadata("accessibility");

const FEATURES = ["feature1", "feature2", "feature3", "feature4", "feature5", "feature6"] as const;

export default async function AccessibilityPage() {
  const t = await getTranslations("accessibility");
  return (
    <>
      <PageHeader title={t("heading")}>
        <p className={styles.lede}>{t("commitment")}</p>
      </PageHeader>
      <h2>{t("standardsHeading")}</h2>
      <p>{t("standardsBody")}</p>
      <h2>{t("featuresHeading")}</h2>
      <ul className={styles.list}>
        {FEATURES.map((f) => (
          <li key={f}>{t(f)}</li>
        ))}
      </ul>
      <h2>{t("limitsHeading")}</h2>
      <p>{t("limitsBody")}</p>
      <h2>{t("reportHeading")}</h2>
      <p>{t("reportBody")}</p>
    </>
  );
}
