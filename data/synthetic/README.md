# data/synthetic — synthetic fixtures only

Everything in this folder is invented. Nothing here comes from, or describes, a real institution or person (guard rails 3–5).

## What counts as synthetic
A value is synthetic only if it was made up for testing and cannot be traced to a real institution, person, document or application. Copying a real value and "changing a digit" is **not** synthetic.

## Naming patterns (use these, nothing else)
| Item | Pattern | Example |
|---|---|---|
| Institution name | `Demo Institute of Technology NN` / `Demo College of Engineering NN` | Demo Institute of Technology 03 |
| Trust / society | `Demo Educational Trust NN` | Demo Educational Trust 03 |
| Application ID | `1-9` + 10 digits (the `1-9…` range is reserved for demo data) | `1-90000004217` |
| Permanent ID | `1-9` + 6 digits | `1-9000317` |
| Faculty / trustee / signatory | tokens only (`fac_tok_…`, `trs_tok_…`, `sig_tok_…`) | `fac_tok_demo_0001` |
| Usernames | `<role>.<region>.demo`, `<role>.demo`, `institution.demoNN` | `rb.southern.demo` |
| Email | `@example.invalid` only (RFC 2606 reserved) | `rb.southern.demo@example.invalid` |
| Licence / certificate numbers | the real *pattern*, demo range `9###` | `9017/RFL/NMSB/2026` |
| Place names | `Demo Town NN`, `Demo District NN` | Demo District 07 |
| Coordinates | inside the sea or a clearly fake grid; never a real campus | — |

## Banned
- Any file from `data/real-samples/` (git-ignored; never enters a cloud session, a commit, a log or an issue).
- Real names, phone numbers, emails, Aadhaar, PAN, DOB, signatures, real application/permanent/faculty IDs.
- Real institution names or website content.
- Real AICTE logos, State Emblem or AICTE branding.

## Guard
CI runs `infra/scripts/real-data-guard.sh` on every push. Values that look like personal-data patterns but are documented synthetic fixtures must be listed in `.real-data-allowlist` with a reason.
