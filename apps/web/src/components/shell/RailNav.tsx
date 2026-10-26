"use client";
// Rail links; the current page gets aria-current="page", which the CSS turns into the saffron bar.
import { usePathname, useSearchParams } from "next/navigation";
import { Link } from "react-aria-components";
import styles from "./AppShell.module.css";

export interface NavItem {
  href: string;
  label: string;
}

export function isCurrent(href: string, pathname: string, view: string | null): boolean {
  const url = new URL(href, "https://satya.invalid");
  if (url.pathname !== pathname) return false;
  return (url.searchParams.get("view") ?? null) === view;
}

export function RailNav({ label, items }: { label: string; items: NavItem[] }) {
  const pathname = usePathname();
  const view = useSearchParams().get("view");
  return (
    <nav aria-label={label}>
      <ul className={styles.railList}>
        {items.map((item) => {
          const current = isCurrent(item.href, pathname, view);
          return (
            <li key={item.href}>
              <Link href={item.href} className={styles.railLink} aria-current={current ? "page" : undefined}>
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
