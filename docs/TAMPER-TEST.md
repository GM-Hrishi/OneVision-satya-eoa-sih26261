# Audit chain tamper test (for a demo video)

Shows that changing one ledger row makes `GET /v1/audit/verify` report `broken` and name the first
bad entry. It runs on a **throwaway in-memory ledger created inside the test**. Never run an edit like
this against the demo database: the runtime database role cannot update or delete ledger rows
(`services/api/tests/test_postgres_store.py` proves it), so the walk-through uses the test only.

## Reproduce

```bash
uv run pytest services/api/tests/test_chain_runs.py -k "tampering or earliest" -v
```

What the tests do (synthetic cases only):

1. Run the checks of two demo cases against an empty in-memory ledger, so it holds a few entries.
2. `GET /v1/audit/verify` returns `{"status": "intact", "first_bad_entry": null, "entries": n}`.
3. Replace one entry's `payload_sha256` (the third entry) in the store's list.
4. `GET /v1/audit/verify` returns `{"status": "broken", "first_bad_entry": 3, ...}`.
5. Put the original entry back: the next call reads `intact` again, because the chain is walked
   again on every call and nothing is cached.

A second test corrupts two entries (one detail text, one hash) and shows the **earliest** bad entry is
the one reported.

## Showing it on screen

Run the command above with `-v -s` in a terminal, or open
`services/api/tests/test_chain_runs.py` next to the output. The endpoint is read-only and writes no
ledger entry. Roles: RB and AU.

The chain rule is `sha256(prev_hash || payload_sha256 || at)` for every row (`services/api/src/satya_api/ledger.py`).
