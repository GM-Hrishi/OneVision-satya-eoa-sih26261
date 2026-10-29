// Self-hosted fonts (no CDN). Fontsource CSS sets font-display: swap.
import "@fontsource/noto-sans/400.css";
import "@fontsource/noto-sans/500.css";
import "@fontsource/noto-sans/700.css";
import "@fontsource/public-sans/800.css";
import "@fontsource/noto-sans-mono/400.css";
import "@fontsource/noto-sans-mono/700.css";
import "@fontsource/noto-sans-devanagari/400.css";
import "@fontsource/noto-sans-devanagari/700.css";
import "@/styles/globals.css";
import type { Metadata } from "next";
import { headers } from "next/headers";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages, getTranslations } from "next-intl/server";
import type { ReactNode } from "react";
import { Providers } from "@/components/Providers";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("app");
  return {
    title: { template: `%s · ${t("name")}`, default: t("name") },
    description: t("description"),
    robots: { index: false, follow: false },
    applicationName: t("name"),
  };
}

export default async function RootLayout({ children }: { children: ReactNode }) {
  const locale = await getLocale();
  const messages = await getMessages();
  // Per-request CSP nonce from src/proxy.ts; React Aria reads it from this meta element.
  const nonce = (await headers()).get("x-nonce") ?? undefined;
  // Client components only need the navigation labels.
  const clientMessages = { nav: messages.nav, error: messages.error, demo: messages.demo, status: messages.status, source: messages.source };
  return (
    <html lang={locale}>
      <head>
        <meta name="csp-nonce" nonce={nonce} />
      </head>
      <body>
        <NextIntlClientProvider locale={locale} messages={clientMessages}>
          <Providers>{children}</Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
