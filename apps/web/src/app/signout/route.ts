// Sign-out: a plain form POST (no JavaScript needed). Clears the Auth.js cookies and sends the
// browser to Keycloak's end-session endpoint, which returns it to the workbench home page.
// CSRF: only same-origin POSTs are accepted (Origin header check) and cookies are SameSite=Lax.
import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";
import { decode } from "next-auth/jwt";

export async function POST(request: NextRequest) {
  const home = new URL(process.env.NEXTAUTH_URL ?? "https://localhost/auth").origin;
  if (request.headers.get("origin") !== home) {
    return new NextResponse(null, { status: 403 });
  }
  const jar = await cookies();
  const sessionCookie = jar.getAll().find((c) => c.name.startsWith("__Secure-next-auth.session-token"));
  let idToken: string | undefined;
  if (sessionCookie && process.env.NEXTAUTH_SECRET) {
    const token = await decode({ token: sessionCookie.value, secret: process.env.NEXTAUTH_SECRET }).catch(() => null);
    idToken = typeof token?.idToken === "string" ? token.idToken : undefined;
  }
  const logout = new URL(`${process.env.KEYCLOAK_ISSUER ?? ""}/protocol/openid-connect/logout`);
  logout.searchParams.set("client_id", process.env.KEYCLOAK_CLIENT_ID ?? "satya-web");
  logout.searchParams.set("post_logout_redirect_uri", `${home}/`);
  if (idToken) logout.searchParams.set("id_token_hint", idToken);
  const response = NextResponse.redirect(logout, 303);
  for (const c of jar.getAll()) {
    if (c.name.includes("next-auth.")) {
      response.cookies.set(c.name, "", { path: "/", maxAge: 0, secure: true, httpOnly: true, sameSite: "lax" });
    }
  }
  return response;
}
