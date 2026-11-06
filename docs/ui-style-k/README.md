# Style K: workbench UI rebuild

Branch: `claude/satya-eoa-ui-style-k-t3pz9w` (the prompt's `feat/ui-style-k` was refused by the remote's email-privacy rule). Scope: `apps/web` plus the docs in this folder. Prompt: `docs/prompts/PROMPT_ui_style_k.md`. Progress: `docs/progress/ui-style-k.md`. Backend seams: `MERGE-NOTES.md`. Contrast: `CONTRAST.md`. Mockups used as reference: `mockups/`.

## What changed
- Tokens: `src/styles/tokens.json` gained the `k`, `dur` and `ease` groups (generated into `tokens.css`; the old groups stay until the legacy modules are gone). Components use tokens only (a test fails on raw hex, gradients or `border-left` in the style K CSS).
- Fonts: Archivo variable (width axis 62 to 125 percent bundled, so no fallback was needed) and JetBrains Mono 500/700, both from Fontsource, no CDN.
- Motion: `src/styles/motion.css` (eight primitives) and `src/lib/motion.ts`. The resting style is always the final state; classes are omitted under reduced motion (unit-tested).
- Shell: top bar with the SATYA mark, nav per role, context text, user menu; breadcrumbs above the page; one-line footer with the chain chip.
- Primitives: `components/k/` (Numeral, Pin, Segmented, Paper, HairRow, LimitationNote, Untrusted) and restyled StatusLabel, SourceTag, risk chip, decision bar.
- Pages: Overview, Queue (+ timeline), Case (+ ladder, evidence map, journey), Affidavit (+ tie lines), Document evidence (new), Manual checks (new), Alerts, Rules (new), Audit (+ integrity, replay check), reuse graph (flagged off).
- Adapters: `src/lib/api/k-adapters/` turn API payloads into view-models; `pending-fields.ts` and `pending-endpoints.ts` are the only places that know about fields not on main.

## The six visuals
| Visual | Where | Data |
|---|---|---|
| 1 Evidence map | Case, "How far each document was checked" | review flags and source checks; no edge without a source |
| 2 Journey | same | review read summary, flags, source and signature checks |
| 3 Tie lines | Affidavit | affidavit-diff ops, expected and sworn declarations |
| 4 Queue timeline | Queue | queue rows, days waiting from `submitted_at` |
| 5 Replay diff | `/audit/replay` | `replay-check` (pending; honest unavailable state) |
| 6 Reuse graph | `/case/[id]/reuse` | fingerprint index (does not exist yet; dev fixture only) |

## Run the checks
```bash
pnpm --filter @satya/web lint && pnpm --filter @satya/web typecheck && pnpm --filter @satya/web test
node apps/web/scripts/contrast-check.mjs
pnpm --filter @satya/web build
```
Browser acceptance (`make e2e`, `make smoke`) needs the Docker stack and was not run in the cloud session that built this branch. Run them before merging.
