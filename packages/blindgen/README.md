# satya-blindgen: independent blind test set

Synthetic data only, generated for this repository. Not real AICTE data. Numbers from this set describe this set and nothing else.

The existing synthetic generators and the rule engines were written together, so perfect scores there prove little. This package generates a randomised set with its own code (layouts, fonts, template years, values, dates, ids, tables, stamp pages, accounts, anomaly combinations including none, one and several per application) and scores the engines against a sealed manifest.

```bash
make eval-blind          # 300 applications, three seeds from blind.config.yaml; writes docs/eval/BLIND-REPORT.md and blind-results.json
make eval-blind-small    # 12 applications (what CI runs)
uv run python -m satya_blindgen generate --out data/blind   # prints the manifest SHA-256
uv run python -m satya_blindgen evaluate --out data/blind --expect-sha <sha>
```

Order: the generator writes `manifest.json` (ground truth: per document the rules that should fire and the expected label, plus hashes of every PDF). Record its SHA-256 before evaluating. The evaluator runs the engines first and opens the manifest only afterwards.

Rule: never change a rule because of a blind result. A test fails if one commit changes `packages/rules/*.yaml` and the blind results together. Misses and false flags are listed in the report, not hidden.

Not planted: land/room reconciliation anomalies, stamp reuse, UDIN reuse, revoked/expired certificates, source-hub states, scan fallback reason codes.
