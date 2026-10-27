// Risk band chip (UI spec §5): text only, caps, never colour alone. The band orders review only.
import { getTranslations } from "next-intl/server";
import type { Band } from "@/lib/demo";
import styles from "./Demo.module.css";

export async function RiskBand({ band }: { band: Band }) {
  const t = await getTranslations("demo");
  return (
    <span className={styles.band} data-band={band}>
      {t(`band.${band}`)}
    </span>
  );
}
