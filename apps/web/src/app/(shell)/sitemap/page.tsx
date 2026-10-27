import Link from "next/link";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/components/ui/PageHeader";
import styles from "@/components/ui/Page.module.css";
import { pageMetadata } from "@/lib/page";

export const generateMetadata = (): Promise<Metadata> => pageMetadata("sitemap");

const WORK = [
  { href: "/overview", key: "overview" },
  { href: "/rb-queue", key: "queue" },
  { href: "/alerts", key: "alerts" },
  { href: "/audit", key: "audit" },
] as const;
const INFO = [
  { href: "/help", key: "help" },
  { href: "/accessibility", key: "accessibility" },
  { href: "/about", key: "about" },
  { href: "/policies", key: "policies" },
  { href: "/sitemap", key: "sitemap" },
] as const;

export default async function SitemapPage() {
  const [t, tNav] = await Promise.all([getTranslations("sitemap"), getTranslations("nav")]);
  return (
    <>
      <PageHeader title={t("heading")} />
      <h2>{t("workHeading")}</h2>
      <ul className={styles.list}>
        {WORK.map((l) => (
          <li key={l.href}>
            <Link href={l.href}>{tNav(l.key)}</Link>
          </li>
        ))}
      </ul>
      <h2>{t("infoHeading")}</h2>
      <ul className={styles.list}>
        {INFO.map((l) => (
          <li key={l.href}>
            <Link href={l.href}>{tNav(l.key)}</Link>
          </li>
        ))}
      </ul>
    </>
  );
}
