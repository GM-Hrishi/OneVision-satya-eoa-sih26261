import { getTranslations } from "next-intl/server";
import styles from "@/components/overview/Overview.module.css";

export default async function Loading() {
  const t = await getTranslations("overview");
  return (
    <div role="status" aria-label={t("loading")} className={styles.grid}>
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className={styles.panel} aria-hidden="true">
          <div className={styles.skelTitle} />
          <div className={styles.skelRow} />
          <div className={styles.skelRow} />
          <div className={styles.skelRow} />
        </div>
      ))}
    </div>
  );
}
