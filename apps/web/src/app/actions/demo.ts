"use server";
// Server actions for the demo flow. The browser never holds the access token: these run on the
// workbench server and call the gateway with the official's token. Next checks the Origin header
// of every server action (CSRF). Errors come back as codes; the page shows plain messages.
import { revalidatePath } from "next/cache";
import { apiPost } from "@/lib/api";
import { ACTIONS, type Action } from "@/lib/demo-types";

const CASE_ID = /^cas_[0-9A-HJKMNP-TV-Z]{26}$/;
const FLAG_ID = /^flg_[0-9A-HJKMNP-TV-Z]{26}$/;
const MAX_PDF = 5 * 1024 * 1024;

export interface FormState {
  ok: boolean;
  code: string | null;
  at?: number;
}

export async function recordDisposition(_prev: FormState, form: FormData): Promise<FormState> {
  const caseId = String(form.get("case_id") ?? "");
  const flagId = String(form.get("flag_id") ?? "");
  const action = String(form.get("action") ?? "");
  const reason = String(form.get("reason") ?? "").trim();
  if (!CASE_ID.test(caseId) || !FLAG_ID.test(flagId)) return { ok: false, code: "NOT_FOUND" };
  if (!(ACTIONS as readonly string[]).includes(action as Action)) return { ok: false, code: "DISPOSITION_ACTION_REJECTED" };
  if (reason.length < 10) return { ok: false, code: "DISPOSITION_REASON_REJECTED" };
  const result = await apiPost(`/v1/cases/${caseId}/flags/${flagId}/disposition`, `/case/${caseId}`, JSON.stringify({ action, reason }), "application/json");
  if (result.ok) revalidatePath(`/case/${caseId}`);
  return { ok: result.ok, code: result.code, at: Date.now() };
}

export async function uploadDocument(_prev: FormState, form: FormData): Promise<FormState> {
  const caseId = String(form.get("case_id") ?? "");
  const slot = String(form.get("slot") ?? "");
  if (!CASE_ID.test(caseId)) return { ok: false, code: "NOT_FOUND" };
  const file = form.get("file");
  if (!(file instanceof File) || file.size === 0) return { ok: false, code: "UPLOAD_SIZE_REJECTED" };
  if (file.size > MAX_PDF) return { ok: false, code: "UPLOAD_SIZE_REJECTED" };
  const query = new URLSearchParams({ slot, filename: file.name }).toString();
  const result = await apiPost(`/v1/cases/${caseId}/documents?${query}`, `/case/${caseId}/upload`, await file.arrayBuffer(), "application/pdf");
  if (result.ok) revalidatePath(`/case/${caseId}`);
  return { ok: result.ok, code: result.code, at: Date.now() };
}

export async function pickDocument(_prev: FormState, form: FormData): Promise<FormState> {
  const caseId = String(form.get("case_id") ?? "");
  const slot = String(form.get("slot") ?? "");
  const source = String(form.get("source_case_id") ?? "");
  if (!CASE_ID.test(caseId) || !CASE_ID.test(source)) return { ok: false, code: "NOT_FOUND" };
  const result = await apiPost(`/v1/cases/${caseId}/documents/pick`, `/case/${caseId}/upload`, JSON.stringify({ slot, source_case_id: source }), "application/json");
  if (result.ok) revalidatePath(`/case/${caseId}`);
  return { ok: result.ok, code: result.code, at: Date.now() };
}
