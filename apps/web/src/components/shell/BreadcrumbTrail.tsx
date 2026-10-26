"use client";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { Breadcrumb, Breadcrumbs, Link } from "react-aria-components";
import { crumbsFor } from "@/lib/rail";
import styles from "./AppShell.module.css";

export function BreadcrumbTrail({ label }: { label: string }) {
  const t = useTranslations("nav");
  const pathname = usePathname();
  const trail = crumbsFor(pathname);
  return (
    <nav aria-label={label} className={styles.crumbs}>
      <Breadcrumbs className={styles.crumbList}>
        <Breadcrumb className={styles.crumb}>
          <Link href="/">{t("home")}</Link>
        </Breadcrumb>
        {trail.map((crumb, i) => (
          <Breadcrumb key={crumb.labelKey} className={styles.crumb}>
            {i === trail.length - 1 ? (
              <Link aria-current="page">{t(crumb.labelKey)}</Link>
            ) : (
              <Link href={crumb.href}>{t(crumb.labelKey)}</Link>
            )}
          </Breadcrumb>
        ))}
      </Breadcrumbs>
    </nav>
  );
}
