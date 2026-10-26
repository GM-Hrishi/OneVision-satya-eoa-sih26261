// AppShell (UI spec §3.1): prototype strip, top strip (breadcrumb, role + region chip, AY chip),
// left rail per role with the saffron current-page bar, GIGW footer.
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import type { ReactNode } from "react";
import { currentSession, primaryRole } from "@/lib/session";
import { RAIL, UTILITY } from "@/lib/rail";
import { setLocale } from "@/app/actions/shell";
import { Suspense } from "react";
import { BreadcrumbTrail } from "./BreadcrumbTrail";
import { MobileMenu } from "./MobileMenu";
import { RailNav } from "./RailNav";
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
  const regionLabel = region === "southern" || region === "national" ? tRegions(region) : tRegions("none");
  const buildDate = process.env.SATYA_BUILD_DATE ?? new Date().toISOString().slice(0, 10);

  return (
    <div className={styles.frame}>
      <a className={styles.skip} href="#main">
        {t("skipLink")}
      </a>
      <p className={styles.prototype}>{t("prototypeStrip")}</p>
      <header className={styles.top}>
        <Link className={styles.brand} href="/">
          {t("brand")}
        </Link>
        <MobileMenu label={t("menu")} closeLabel={t("closeMenu")} items={[...items, ...utility]} />
        <Suspense>
          <BreadcrumbTrail label={t("breadcrumbLabel")} />
        </Suspense>
        <div className={styles.chips}>
          {role && (
            <span className={styles.chip}>{t("roleChip", { role: tRoles(role), region: regionLabel })}</span>
          )}
          <span className={styles.chip}>{t("ayChip", { ay: CURRENT_AY })}</span>
          {session ? (
            <form method="post" action="/signout" className={styles.inline}>
              <span className={styles.user}>{t("signedInAs", { user: session.user.name })}</span>
              <button type="submit" className={styles.textButton}>
                {t("signOut")}
              </button>
            </form>
          ) : (
            <Link className={styles.textButton} href="/signin">
              {t("signIn")}
            </Link>
          )}
        </div>
      </header>
      <div className={styles.body}>
        <aside className={styles.rail}>
          <Suspense>{items.length > 0 && <RailNav label={t("railLabel")} items={items} />}</Suspense>
          <div className={styles.railBottom}>
            <Suspense>
              <RailNav label={t("utilityLabel")} items={utility} />
            </Suspense>
            <LanguageSwitcher path={path} locale={locale} label={t("languageLabel")} english={t("english")} hindi={t("hindi")} />
          </div>
        </aside>
        <main id="main" className={styles.main} tabIndex={-1}>
          {children}
        </main>
      </div>
      <footer className={styles.footer}>
        <nav aria-label={tFooter("label")}>
          <ul className={styles.footerLinks}>
            <li><Link href="/about">{tFooter("about")}</Link></li>
            <li><Link href="/policies">{tFooter("policies")}</Link></li>
            <li><Link href="/help">{tFooter("help")}</Link></li>
            <li><Link href="/accessibility">{tFooter("accessibility")}</Link></li>
            <li><Link href="/sitemap">{tFooter("sitemap")}</Link></li>
          </ul>
        </nav>
        <div className={styles.footerLang}>
          <LanguageSwitcher path={path} locale={locale} label={t("languageLabel")} english={t("english")} hindi={t("hindi")} />
        </div>
        <p className={styles.footerMeta}>{tFooter("lastUpdated", { date: buildDate })}</p>
        <p className={styles.footerMeta}>{tFooter("disclaimer")}</p>
        <p className={styles.footerMeta}>{tFooter("team", { year: new Date().getFullYear() })}</p>
      </footer>
    </div>
  );
}

function LanguageSwitcher(props: { path: string; locale: string; label: string; english: string; hindi: string }) {
  return (
    <form action={setLocale} className={styles.lang} aria-label={props.label}>
      <input type="hidden" name="back" value={props.path} />
      <button type="submit" name="locale" value="en" lang="en" aria-pressed={props.locale === "en"} className={styles.langButton}>
        {props.english}
      </button>
      <span aria-hidden="true">|</span>
      <button type="submit" name="locale" value="hi" lang="hi" aria-pressed={props.locale === "hi"} className={styles.langButton}>
        {props.hindi}
      </button>
    </form>
  );
}
