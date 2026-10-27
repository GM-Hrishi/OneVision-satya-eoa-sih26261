// Opens an alert's flag or document and marks the alert as seen (a short HttpOnly cookie in this
// browser). The target is rebuilt from validated ids, never taken from the query, so this cannot be
// used as an open redirect.
import { NextResponse, type NextRequest } from "next/server";
import { ALERT_KEY, parseSeen, SEEN_COOKIE, SEEN_MAX } from "@/lib/alerts";
import { currentSession } from "@/lib/session";

const CASE_ID = /^cas_[0-9A-HJKMNP-TV-Z]{26}$/;
const FLAG_ID = /^flg_[0-9A-HJKMNP-TV-Z]{26}$/;

export async function GET(request: NextRequest) {
  const origin = new URL(process.env.NEXTAUTH_URL ?? "https://localhost/auth").origin;
  const session = await currentSession();
  if (!session?.user.roles.includes("RB")) return NextResponse.redirect(new URL("/signin?callbackUrl=%2Falerts", origin), 303);
  const { searchParams } = request.nextUrl;
  const key = searchParams.get("key") ?? "";
  const caseId = searchParams.get("case") ?? "";
  const flag = searchParams.get("flag") ?? "";
  if (!ALERT_KEY.test(key) || !CASE_ID.test(caseId) || (flag && !FLAG_ID.test(flag))) {
    return NextResponse.redirect(new URL("/alerts", origin), 303);
  }
  const target = new URL(`/case/${caseId}#${flag ? `flag-${flag}` : "docs"}`, origin);
  const response = NextResponse.redirect(target, 303);
  const seen = parseSeen(request.cookies.get(SEEN_COOKIE)?.value).filter((k) => k !== key);
  response.cookies.set(SEEN_COOKIE, [...seen, key].slice(-SEEN_MAX).join(","), {
    path: "/",
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 30,
  });
  return response;
}
