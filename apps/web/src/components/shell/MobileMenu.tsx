"use client";
// Below 1024px the rail becomes a menu button (UI spec §3.1).
import { Button, Dialog, DialogTrigger, Heading, Link, Popover } from "react-aria-components";
import type { NavItem } from "./RailNav";
import styles from "./AppShell.module.css";

export function MobileMenu({ label, closeLabel, items }: { label: string; closeLabel: string; items: NavItem[] }) {
  return (
    <div className={styles.mobileMenu}>
      <DialogTrigger>
        <Button className={styles.menuButton}>{label}</Button>
        <Popover className={styles.menuPopover} placement="bottom start">
          <Dialog className={styles.menuDialog}>
            {({ close }) => (
              <>
                <Heading slot="title" className={styles.visuallyHidden}>
                  {label}
                </Heading>
                <ul className={styles.menuList}>
                  {items.map((item) => (
                    <li key={item.href}>
                      <Link href={item.href} className={styles.menuLink} onPress={close}>
                        {item.label}
                      </Link>
                    </li>
                  ))}
                </ul>
                <Button className={styles.textButton} onPress={close}>
                  {closeLabel}
                </Button>
              </>
            )}
          </Dialog>
        </Popover>
      </DialogTrigger>
    </div>
  );
}
