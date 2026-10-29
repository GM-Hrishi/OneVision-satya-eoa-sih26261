// Sign-in through Keycloak (OIDC authorization code + PKCE) with next-auth v4.
// The session is an encrypted (JWE), HttpOnly, Secure, SameSite=Lax cookie; tokens never reach
// browser JavaScript. The access token (5 min, Keycloak default) is kept inside that cookie so the
// workbench server can call the gateway's Workbench API on the official's behalf (src/lib/api.ts);
// no refresh token is stored. When it expires the official is sent through a silent SSO renewal. Discovery uses the internal Keycloak URL, so the browser gets the public
// authorization endpoint while token/JWKS calls stay on the private network.
import type { NextAuthOptions } from "next-auth";
import KeycloakProvider from "next-auth/providers/keycloak";

const SESSION_MAX_AGE_S = 30 * 60; // matches the realm's SSO idle timeout

export const ROLES = ["RB", "SC", "EV", "HC", "RA", "AU", "INS"] as const;
export type Role = (typeof ROLES)[number];

interface KeycloakProfile {
  sub: string;
  preferred_username?: string;
  name?: string; // display name from the realm's `profile` scope, e.g. "RB Officer 01"
  roles?: string[];
  groups?: string[];
}

function env(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is not set`);
  return value;
}

export function authOptions(): NextAuthOptions {
  return {
    secret: env("NEXTAUTH_SECRET"),
    session: { strategy: "jwt", maxAge: SESSION_MAX_AGE_S, updateAge: 5 * 60 },
    useSecureCookies: true,
    pages: { signIn: "/signin", error: "/signin" },
    providers: [
      KeycloakProvider({
        clientId: env("KEYCLOAK_CLIENT_ID"),
        clientSecret: env("KEYCLOAK_CLIENT_SECRET"),
        issuer: env("KEYCLOAK_ISSUER"),
        wellKnown: `${env("KEYCLOAK_INTERNAL_URL")}/.well-known/openid-configuration`,
        checks: ["pkce", "state"],
        authorization: { params: { scope: "openid" } },
        profile(profile: KeycloakProfile) {
          return { id: profile.sub, name: profile.preferred_username ?? profile.sub };
        },
      }),
    ],
    callbacks: {
      async jwt({ token, account, profile }) {
        if (account && profile) {
          const kc = profile as KeycloakProfile;
          token.username = kc.preferred_username ?? kc.sub;
          token.displayName = kc.name;
          token.roles = (kc.roles ?? []).filter((r): r is Role => (ROLES as readonly string[]).includes(r));
          token.regions = (kc.groups ?? [])
            .filter((g) => g.startsWith("/regions/"))
            .map((g) => g.slice("/regions/".length));
          token.idToken = account.id_token;
          token.accessToken = account.access_token;
          token.accessTokenExpires = account.expires_at;
        }
        return token;
      },
      async session({ session, token }) {
        // Only what the UI needs; no tokens in the session object.
        return {
          expires: session.expires,
          user: {
            name: String(token.displayName ?? token.username ?? ""),
            roles: (token.roles as Role[] | undefined) ?? [],
            regions: (token.regions as string[] | undefined) ?? [],
          },
        };
      },
    },
  };
}
