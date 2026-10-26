// Case views that exist in this build (UI spec §0.3: every view of a case at most two clicks away).
// Only built screens are listed, so there is no dead navigation; later tabs (Summary, Documents,
// Year-over-year, Audit) join with their slices.
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import styles from "./CaseTabs.module.css";

const TABS = [
  { segment: "affidavit", labelKey: "affidavit" },
  { segment: "verification", labelKey: "verification" },
] as const;

export async function CaseTabs({ caseId, current }: { caseId: string; current: (typeof TABS)[number]["segment"] }) {
  const t = await getTranslations("nav");
  const tv = await getTranslations("verification");
  return (
    <nav aria-label={tv("tabsLabel")} className={styles.tabs}>
      <ul>
        {TABS.map((tab) => (
          <li key={tab.segment}>
            <Link
              href={`/case/${caseId}/${tab.segment}`}
              aria-current={tab.segment === current ? "page" : undefined}
              className={styles.tab}
            >
              {t(tab.labelKey)}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
