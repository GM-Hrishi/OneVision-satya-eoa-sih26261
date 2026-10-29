// Per-request CSP nonce (Next 16 "proxy", formerly middleware). Next reads the nonce from the
// request's Content-Security-Policy header and applies it to its own scripts.
import { NextResponse, type NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.getRandomValues(new Uint8Array(16))).toString("base64");
  const dev = process.env.NODE_ENV === "development";
  const authOrigin = new URL(process.env.KEYCLOAK_ISSUER ?? "https://auth.localhost").origin;
  const csp = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${dev ? " 'unsafe-eval'" : ""}`,
    `style-src 'self' 'nonce-${nonce}'`,
    // React Aria sets a few inline style attributes (e.g. visually hidden text).
    "style-src-attr 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self'",
    "connect-src 'self'",
    // PDF.js runs its parser in a worker served from this origin.
    "worker-src 'self' blob:",
    `form-action 'self' ${authOrigin}`,
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "object-src 'none'",
    "upgrade-insecure-requests",
  ].join("; ");
  const headers = new Headers(request.headers);
  headers.set("x-nonce", nonce);
  headers.set("x-pathname", request.nextUrl.pathname + request.nextUrl.search);
  headers.set("Content-Security-Policy", csp);
  const response = NextResponse.next({ request: { headers } });
  response.headers.set("Content-Security-Policy", csp);
  response.headers.set("X-Robots-Tag", "noindex, nofollow"); // internal tool: also for non-HTML routes
  return response;
}

export const config = {
  matcher: [
    { source: "/((?!_next/static|_next/image|healthz|icon.svg|robots.txt).*)", missing: [{ type: "header", key: "next-router-prefetch" }] },
  ],
};
