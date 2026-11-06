"use client";
// Top-bar nav links (the file keeps its old name until the T14 clean-up). The current page gets aria-current="page", which the CSS turns into an accent underline.
import { usePathname } from "next/navigation";
import { Link } from "react-aria-components";
import styles from "./AppShell.module.css";

export interface NavItem {
  href: string;
  label: string;
}

export function isCurrent(href: string, pathname: string): boolean {
  return new URL(href, "https://satya.invalid").pathname === pathname;
}

export function RailNav({ label, items }: { label: string; items: NavItem[] }) {
  const pathname = usePathname();
  return (
    <nav aria-label={label} className={styles.topNav}>
      <ul className={styles.navList}>
        {items.map((item) => {
          const current = isCurrent(item.href, pathname);
          return (
            <li key={item.href}>
              <Link href={item.href} className={styles.navLink} aria-current={current ? "page" : undefined}>
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
