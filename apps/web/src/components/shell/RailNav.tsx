"use client";
// Rail links; the current page gets aria-current="page", which the CSS turns into the saffron bar.
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
    <nav aria-label={label}>
      <ul className={styles.railList}>
        {items.map((item) => {
          const current = isCurrent(item.href, pathname);
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
