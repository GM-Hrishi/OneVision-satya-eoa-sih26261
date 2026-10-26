// Server-side authorisation helpers. Every protected page calls one of these; the client is never
// trusted to decide access.
import { getServerSession, type Session } from "next-auth";
import { forbidden, redirect } from "next/navigation";
import { authOptions, type Role } from "./auth";

export async function currentSession(): Promise<Session | null> {
  return getServerSession(authOptions());
}

export async function requireSession(callbackPath: string): Promise<Session> {
  const session = await currentSession();
  if (!session) redirect(`/signin?callbackUrl=${encodeURIComponent(callbackPath)}`);
  return session;
}

export async function requireRole(role: Role, callbackPath: string): Promise<Session> {
  const session = await requireSession(callbackPath);
  if (!session.user.roles.includes(role)) forbidden();
  return session;
}

/** Workbench roles in priority order; INS has no workbench (UI spec §1). */
export function primaryRole(session: Session): Role | null {
  const order: Role[] = ["RB", "AU", "RA", "SC", "EV", "HC"];
  return order.find((r) => session.user.roles.includes(r)) ?? null;
}
