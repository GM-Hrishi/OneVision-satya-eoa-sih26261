// SH-01: role home redirect.
import { redirect } from "next/navigation";
import { primaryRole, requireSession } from "@/lib/session";

export default async function RoleHomeRedirect() {
  const session = await requireSession("/");
  const role = primaryRole(session);
  if (role === "RB") redirect("/overview");
  redirect("/home");
}
