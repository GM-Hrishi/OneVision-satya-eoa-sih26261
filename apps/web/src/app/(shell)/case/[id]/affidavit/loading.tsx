import { getTranslations } from "next-intl/server";
import styles from "@/components/ui/Page.module.css";

export default async function Loading() {
  const t = await getTranslations("diff");
  return (
    <div className={styles.skeleton} role="status" aria-label={t("loading")}>
      <div className={styles.skeletonRow} />
      <div className={styles.skeletonRow} />
      <div className={styles.skeletonRow} />
    </div>
  );
}
