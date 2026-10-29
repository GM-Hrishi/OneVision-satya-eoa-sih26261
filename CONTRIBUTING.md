# Contributing to SATYA-EoA

Thank you for your interest. SATYA-EoA is a decision-support prototype: it advises, and officials decide. Contributions must keep it that way.

## Ground rules

- **Synthetic data only.** Never add real documents, real application or faculty identifiers, personal data (names, phone numbers, emails, Aadhaar, PAN, signatures) or real institution names to code, tests, fixtures, screenshots or docs. Follow the naming patterns in [data/synthetic/README.md](data/synthetic/README.md). `data/real-samples/` is git-ignored and must stay empty in the repository.
- **AI advises, humans decide.** Do not add an approve, reject or auto-clear control, and do not make any output carry regulatory effect. Outbound events stay marked `advisory: true` and `regulatory_effect: "none"`.
- **Mock portal only.** Do not claim or add a real connection to AICTE, CCA, SHCIL, ICAI or any issuer.
- **No secrets.** Secrets live in `.env`, which is git-ignored.
- **No foreign LLM APIs in the product.**
- Every rule and flag cites the Handbook clause it comes from; mark anything unconfirmed `[VERIFY]`.
- Do not show status by colour alone; always include a text label.

## How to contribute

1. Open an issue or comment on one before starting anything large.
2. One pull request per change, kept small and focused.
3. Add or update tests and docs with the change.
4. CI must pass before review.

## Running the checks

From the repository root (no running stack needed):

```bash
pnpm install --frozen-lockfile && uv sync --all-packages --frozen
make lint
make typecheck
make test
make guard
```

`make guard` is the real-data guard and `make secret-scan` runs gitleaks (needs Docker). `make synth-check` fails if the committed synthetic cases are stale; regenerate them with `make synth`. If you change a schema in `packages/shared-types/schemas/`, run `make gen-types` and commit the generated code.

The full stack, smoke tests and browser acceptance need Docker; see [docs/DEV-SETUP.md](docs/DEV-SETUP.md).

## Licence

By contributing you agree that your contribution is licensed under the Apache License 2.0 (see [LICENSE](LICENSE)).
