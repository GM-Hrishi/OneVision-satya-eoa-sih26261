import type { Metadata } from "next";
import { headers } from "next/headers";
import { getTranslations } from "next-intl/server";

/** Unique title + meta description for a page, from the page's message namespace. */
export async function pageMetadata(namespace: string, titleKey = "title", descriptionKey = "description"): Promise<Metadata> {
  const t = await getTranslations(namespace);
  return { title: t(titleKey), description: t(descriptionKey) };
}

/** The current path (set by src/proxy.ts), for return links such as the language switcher. */
export async function currentPath(): Promise<string> {
  return (await headers()).get("x-pathname") ?? "/";
}
