# AGENT_BOARD

Shared notes between coding agents and the owner. Read this FIRST in every session. Append, never rewrite old entries.
Before stopping, add a handoff note (what is done, what is next, blockers). Parallel agents use separate git worktrees.

Entry format: `- <UTC timestamp> | <agent / branch> | <what finished> | <open questions or blockers>`

## Log
- 2026-11-06T07:00Z | logic run, `feat/logic-rival-parity` (PR #15, draft) | Backend rival-parity work done (limitation keys, why_detail, audit/replay/run-diff endpoints, certificate coverage, API examples in docs/api-examples). Last commit f9768ee. | None.
- 2026-11-06T07:10Z | UI run, `claude/satya-eoa-ui-style-k-t3pz9w` (PR #16, draft) | Style K rebuild T0 to T14 done, not browser-tested. Branch name is `claude/...` because the remote refused `feat/ui-style-k` (email privacy). | Manual-task list and resolve contract deferred past Update day. /rules headline needs a rule-list endpoint.
- 2026-11-06T07:20Z | fix session, same UI branch | Lockfile specifier mismatch fixed (523d299). CI green except Stack smoke test. | Smoke failure was one e2e check, "switches to Hindi": the queue H1 is now a headline sentence, so the test asserted an old title. Test now checks for Devanagari.

## Handoff (current)
- NEXT (Sat 7 Nov, owner on laptop): run the UI branch with `WITH_OCR=1 make up`, `make demo-reset`, `make e2e`, `make smoke`; send screenshots. Then one join run: integration branch merging logic then UI, fill `apps/web/.../pending-endpoints.ts`, follow `docs/ui-style-k/MERGE-NOTES.md`.
- Decision point Sat evening: record the video on the K build only if merged to `main`, smoke green and mirrored in the public repo; otherwise record on `main` (a652b6d).
- Do not merge PR #15 or #16 before Update day (8 Nov) without the owner's say.
