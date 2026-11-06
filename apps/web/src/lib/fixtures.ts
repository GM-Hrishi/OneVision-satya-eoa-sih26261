// Dev fixtures (prompt guardrail 4): only when NEXT_PUBLIC_UI_FIXTURES=1 AND this is not a production build.
// scripts/check-fixtures.mjs fails `pnpm build` if the variable is set, so production can never show fixtures.
export function uiFixtures(): boolean {
  return process.env.NEXT_PUBLIC_UI_FIXTURES === "1" && process.env.NODE_ENV !== "production";
}
