import { getTranslations } from "next-intl/server";
import styles from "@/components/demo/Demo.module.css";

export default async function Loading() {
  const t = await getTranslations("demo");
  return (
    <div role="status" aria-label={t("loading")}>
      <div className={styles.skeletonBlock} />
      <div className={styles.skeletonBlock} />
    </div>
  );
}
