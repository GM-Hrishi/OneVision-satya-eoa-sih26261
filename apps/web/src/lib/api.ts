// Server-side client for the gateway's Workbench API (Portal spec §2.0). Runs only on the workbench
// server: the official's access token is read from the encrypted session cookie and sent as a Bearer
// token over the internal network. The browser never sees the token or the API origin.
import { cookies } from "next/headers";
import { forbidden, notFound, redirect } from "next/navigation";
import { getToken } from "next-auth/jwt";

const EXPIRY_MARGIN_S = 15;
const TIMEOUT_MS = 20_000;

function renew(callbackPath: string): never {
  redirect(`/signin?renew=1&callbackUrl=${encodeURIComponent(callbackPath)}`);
}

async function accessToken(): Promise<string | null> {
  const jar = await cookies();
  const token = await getToken({ req: { cookies: jar, headers: {} } as never, secureCookie: true }).catch(() => null);
  if (!token?.accessToken || !token.accessTokenExpires) return null;
  if (token.accessTokenExpires - EXPIRY_MARGIN_S <= Date.now() / 1000) return null;
  return token.accessToken;
}

export class ApiUnavailable extends Error {
  constructor(readonly status: number) {
    super(`Workbench API answered ${status}`);
  }
}

/** GET a Workbench API path. 401 → silent SSO renewal, 403 → "Not assigned to you", 404 → not found. */
export async function apiGet<T>(path: string, callbackPath: string): Promise<T> {
  const token = await accessToken();
  if (!token) renew(callbackPath);
  const base = process.env.SATYA_API_INTERNAL_URL ?? "http://api:8000";
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, {
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      cache: "no-store",
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch {
    throw new ApiUnavailable(0);
  }
  if (response.status === 401) renew(callbackPath);
  if (response.status === 403) forbidden();
  if (response.status === 404) notFound();
  if (!response.ok) throw new ApiUnavailable(response.status);
  return (await response.json()) as T;
}
