"use client";
// UserMenu (UI spec §3.1, v0.8): initials, display name and a chevron as one plain button. The menu
// holds the identity block (not focusable), Language, Accessibility settings and Sign out.
// Escape closes it and returns focus to the trigger (React Aria). Sign out posts to /signout,
// which ends the Keycloak session.
import { useRef, useTransition } from "react";
import { Button, Header, Menu, MenuItem, MenuSection, MenuTrigger, Popover, Separator } from "react-aria-components";
import { setLocale } from "@/app/actions/shell";
import { Icon } from "@/components/ui/Icon";
import styles from "./UserMenu.module.css";

export interface UserMenuText {
  menu: string;
  role: string;
  region: string;
  language: string;
  english: string;
  hindi: string;
  accessibility: string;
  signOut: string;
}

function initials(name: string): string {
  const parts = name.split(/[^A-Za-z0-9]+/).filter(Boolean);
  const letters = parts.length > 1 ? `${parts[0]?.[0] ?? ""}${parts[1]?.[0] ?? ""}` : (parts[0] ?? "?").slice(0, 2);
  return letters.toUpperCase();
}

export function UserMenu({ name, locale, path, text }: { name: string; locale: "en" | "hi"; path: string; text: UserMenuText }) {
  const form = useRef<HTMLFormElement>(null);
  const [, start] = useTransition();
  const chooseLanguage = (next: string) => {
    const data = new FormData();
    data.set("locale", next);
    data.set("back", path);
    start(() => setLocale(data));
  };
  return (
    <>
      <MenuTrigger>
        <Button className={styles.trigger} aria-label={`${text.menu}: ${name}`}>
          <span className={styles.initials} data-initials={initials(name)} aria-hidden="true" />
          <span className={styles.name}>{name}</span>
          <Icon name="chevron-down" size={14} />
        </Button>
        <Popover className={styles.popover} placement="bottom end">
          <div className={styles.identity}>
            <span className={styles.identityName}>{name}</span>
            <span>{text.role}</span>
            <span>{text.region}</span>
          </div>
          <Menu className={styles.menu} aria-label={text.menu} onAction={(key) => key === "signout" && form.current?.requestSubmit()}>
            <MenuSection
              selectionMode="single"
              selectedKeys={[locale]}
              disallowEmptySelection
              onSelectionChange={(keys) => {
                const next = [...keys][0];
                if (next === "en" || next === "hi") chooseLanguage(next);
              }}
            >
              <Header className={styles.sectionHead}>{text.language}</Header>
              <MenuItem id="en" className={styles.item} textValue={text.english}>
                {text.english}
              </MenuItem>
              <MenuItem id="hi" className={styles.item} textValue={text.hindi}>
                <span lang="hi">{text.hindi}</span>
              </MenuItem>
            </MenuSection>
            <Separator className={styles.separator} />
            <MenuItem id="accessibility" className={styles.item} href="/accessibility" textValue={text.accessibility}>
              {text.accessibility}
            </MenuItem>
            <Separator className={styles.separator} />
            <MenuItem id="signout" className={styles.item} textValue={text.signOut}>
              {text.signOut}
            </MenuItem>
          </Menu>
        </Popover>
      </MenuTrigger>
      <form ref={form} method="post" action="/signout" hidden />
    </>
  );
}
