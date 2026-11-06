// AppShell (style K): one top bar (product mark, nav per role, context text, search, user menu), breadcrumbs above the
// page, one-line footer with the chain chip. The left rail is retired; below 1024px the nav is a menu button.
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import type { ReactNode } from "react";
import { currentSession, primaryRole } from "@/lib/session";
import { RAIL, UTILITY } from "@/lib/rail";
import { Suspense } from "react";
import { BreadcrumbTrail } from "./BreadcrumbTrail";
import { MobileMenu } from "./MobileMenu";
import { RailNav } from "./RailNav";
import { UserMenu } from "./UserMenu";
import { ChainChip } from "./ChainChip";
import styles from "./AppShell.module.css";

const CURRENT_AY = "2026-27";

export async function AppShell({ children, path = "/" }: { children: ReactNode; path?: string }) {
  const [t, tNav, tRoles, tRegions, tFooter, locale, session] = await Promise.all([
    getTranslations("shell"),
    getTranslations("nav"),
    getTranslations("roles"),
    getTranslations("regions"),
    getTranslations("footer"),
    getLocale(),
    currentSession(),
  ]);
  const role = session ? primaryRole(session) : null;
  const rail = (role && RAIL[role]) || [];
  const items = rail.map((i) => ({ href: i.href, label: tNav(i.labelKey) }));
  const utility = UTILITY.map((i) => ({ href: i.href, label: tNav(i.labelKey) }));
  const region = session?.user.regions[0];
  const regionLabel = region === "southern" || region === "national" ? t("regionName", { region: tRegions(region) }) : tRegions("none");
  const roleLabel = role ? tRoles(role) : "";
  const built = process.env.SATYA_BUILD_DATE ?? new Date().toISOString().slice(0, 10);
  // Build metadata as e.g. "27 Oct 2026" (UTC, so the day does not move with the server's zone).
  const buildDate = new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(
    new Date(`${built}T00:00:00Z`),
  );

  return (
    <div className={`${styles.frame} k-surface`}>
      <a className={styles.skip} href="#main">
        {t("skipLink")}
      </a>
      <header className={styles.top}>
        <Link className={styles.brand} href="/" aria-label={t("brand")}>
          <span aria-hidden="true">{t("brandName")}</span>
          <span className={styles.dot} aria-hidden="true" />
          <span aria-hidden="true" className={styles.brandEoa}>
            {t("brandSuffix")}
          </span>
        </Link>
        <Suspense>{items.length > 0 && <RailNav label={t("railLabel")} items={items} />}</Suspense>
        <MobileMenu label={t("menu")} closeLabel={t("closeMenu")} items={[...items, ...utility]} />
        <div className={styles.headRight}>
          {role && (
            <div className={styles.context} role="group" aria-label={t("contextAria", { role: roleLabel, region: regionLabel, ay: CURRENT_AY })}>
              <span>{t("contextRole", { role: roleLabel, region: regionLabel })}</span>
              <span className={styles.bar} aria-hidden="true">
                |
              </span>
              <span>{t("contextAy", { ay: CURRENT_AY })}</span>
            </div>
          )}
          {role === "RB" && (
            <form role="search" action="/rb-queue" method="get" className={styles.search}>
              <label className={styles.visuallyHidden} htmlFor="site-search">
                {t("searchLabel")}
              </label>
              <input id="site-search" className={styles.searchInput} type="search" name="q" maxLength={40} placeholder={t("searchPlaceholder")} autoComplete="off" />
              <button type="submit" className={styles.searchButton}>
                {t("searchButton")}
              </button>
            </form>
          )}
          {session ? (
            <UserMenu
              name={session.user.name}
              locale={locale === "hi" ? "hi" : "en"}
              path={path}
              text={{
                menu: t("userMenu"),
                role: roleLabel,
                region: regionLabel,
                language: t("languageLabel"),
                english: t("english"),
                hindi: t("hindi"),
                accessibility: t("accessibilitySettings"),
                signOut: t("signOut"),
              }}
            />
          ) : (
            <Link className={styles.textButton} href="/signin">
              {t("signIn")}
            </Link>
          )}
        </div>
      </header>
      <div className={styles.body}>
        <Suspense>
          <BreadcrumbTrail label={t("breadcrumbLabel")} />
        </Suspense>
        <main id="main" className={styles.main} tabIndex={-1}>
          {children}
        </main>
      </div>
      <footer className={styles.footer}>
        <Suspense fallback={<p className={styles.chain} aria-hidden="true" />}>
          <ChainChip />
        </Suspense>
        <nav aria-label={tFooter("label")}>
          <ul className={styles.footerLinks}>
            <li>
              <Link href="/policies">{tFooter("policies")}</Link>
            </li>
            <li>
              <Link href="/accessibility">{tFooter("accessibility")}</Link>
            </li>
            <li>
              <Link href="/help">{tFooter("help")}</Link>
            </li>
            <li>
              <Link href="/sitemap">{tFooter("sitemap")}</Link>
            </li>
          </ul>
        </nav>
        <p className={styles.footerMeta}>{tFooter("advisory", { date: buildDate })}</p>
      </footer>
    </div>
  );
}
