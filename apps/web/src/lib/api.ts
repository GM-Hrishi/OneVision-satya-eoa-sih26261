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

/** GET that never redirects or throws: null when there is no usable session or the API fails.
 *  For optional page furniture (the rail alert card) that must not break the page around it. */
const QUIET_TTL_MS = 20_000;
const quietCache = new Map<string, { at: number; data: unknown }>();

export async function apiGetQuiet<T>(path: string): Promise<T | null> {
  const token = await accessToken();
  if (!token) return null;
  // Every page renders the rail card, so answers are reused for a few seconds per session; this
  // keeps the card from eating the official's per-minute API quota.
  const key = `${token.slice(-32)}|${path}`;
  const hit = quietCache.get(key);
  if (hit && Date.now() - hit.at < QUIET_TTL_MS) return hit.data as T;
  const base = process.env.SATYA_API_INTERNAL_URL ?? "http://api:8000";
  try {
    const response = await fetch(`${base}${path}`, {
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      cache: "no-store",
      signal: AbortSignal.timeout(5_000),
    });
    if (!response.ok) return null;
    const data = (await response.json()) as T;
    if (quietCache.size > 200) quietCache.clear();
    quietCache.set(key, { at: Date.now(), data });
    return data;
  } catch {
    return null;
  }
}

export interface ApiResult<T> {
  ok: boolean;
  status: number;
  data: T | null;
  code: string | null;
}

/** POST to the Workbench API from a server action. Never throws on 4xx: the caller shows `code`. */
export async function apiPost<T>(path: string, callbackPath: string, body: BodyInit, contentType: string): Promise<ApiResult<T>> {
  const token = await accessToken();
  if (!token) renew(callbackPath);
  const base = process.env.SATYA_API_INTERNAL_URL ?? "http://api:8000";
  try {
    const response = await fetch(`${base}${path}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": contentType, Accept: "application/json" },
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (response.status === 401) renew(callbackPath);
    const data = (await response.json().catch(() => null)) as (T & { code?: string }) | null;
    return { ok: response.ok, status: response.status, data: response.ok ? data : null, code: response.ok ? null : (data?.code ?? "INTERNAL_ERROR") };
  } catch {
    return { ok: false, status: 0, data: null, code: "UNAVAILABLE" };
  }
}

/** GET raw bytes (a stored PDF) for the viewer route. Same status mapping as apiGet. */
export async function apiBytes(path: string, callbackPath: string): Promise<{ bytes: ArrayBuffer; type: string }> {
  const token = await accessToken();
  if (!token) renew(callbackPath);
  const base = process.env.SATYA_API_INTERNAL_URL ?? "http://api:8000";
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, {
      headers: { Authorization: `Bearer ${token}` },
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
  return { bytes: await response.arrayBuffer(), type: response.headers.get("content-type") ?? "application/pdf" };
}
