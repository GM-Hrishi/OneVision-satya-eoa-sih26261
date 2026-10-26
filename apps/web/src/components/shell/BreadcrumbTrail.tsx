"use client";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { Breadcrumb, Breadcrumbs, Link } from "react-aria-components";
import { CRUMBS } from "@/lib/rail";
import styles from "./AppShell.module.css";

export function BreadcrumbTrail({ label }: { label: string }) {
  const t = useTranslations("nav");
  const pathname = usePathname();
  const trail = CRUMBS[pathname] ?? [];
  return (
    <nav aria-label={label} className={styles.crumbs}>
      <Breadcrumbs className={styles.crumbList}>
        <Breadcrumb className={styles.crumb}>
          <Link href="/">{t("home")}</Link>
        </Breadcrumb>
        {trail.map((key, i) => (
          <Breadcrumb key={key} className={styles.crumb}>
            {i === trail.length - 1 ? <Link aria-current="page">{t(key)}</Link> : <Link>{t(key)}</Link>}
          </Breadcrumb>
        ))}
      </Breadcrumbs>
    </nav>
  );
}
