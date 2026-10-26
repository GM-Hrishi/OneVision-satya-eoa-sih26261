"use server";
// Server actions are POST-only and Next checks the Origin header against the host, which is
// the CSRF protection for these forms.
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { LOCALE_COOKIE, toLocale } from "@/i18n/locale";

export async function setLocale(formData: FormData): Promise<void> {
  const locale = toLocale(String(formData.get("locale") ?? ""));
  const back = String(formData.get("back") ?? "/");
  (await cookies()).set(LOCALE_COOKIE, locale, {
    path: "/",
    sameSite: "lax",
    secure: true,
    httpOnly: true,
    maxAge: 60 * 60 * 24 * 365,
  });
  redirect(back.startsWith("/") && !back.startsWith("//") ? back : "/");
}
