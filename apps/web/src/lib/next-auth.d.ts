import type { Role } from "./auth";

declare module "next-auth" {
  interface Session {
    user: { name: string; roles: Role[]; regions: string[] };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    username?: string;
    displayName?: string;
    roles?: Role[];
    regions?: string[];
    idToken?: string;
    accessToken?: string;
    accessTokenExpires?: number; // seconds since the epoch
  }
}
