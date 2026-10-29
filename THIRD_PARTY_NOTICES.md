# Third-party notices

SATYA-EoA is licensed under the Apache License 2.0 (see `LICENSE` and `NOTICE`). It depends on the open-source packages listed below, each under its own licence. This file lists name, version and licence for direct and transitive dependencies.

How it was generated (2026-10-29): npm packages with `pnpm licenses list --json` and `pnpm licenses list --prod --json` after `pnpm install --frozen-lockfile`; Python packages with `pip-licenses --format=json --with-urls` run against the environment created by `uv sync --all-packages --frozen`. Licence names are copied from each package's metadata and have not been reviewed one by one by a lawyer. [VERIFY: legal review before relying on this list]

## Licences that need attention

No AGPL, GPL, SSPL or non-commercial licence was found in the npm or Python dependency sets. PyMuPDF and Ultralytics (AGPL) are not present. The following weak-copyleft or unreviewed entries are present:

| Package | Version | Licence | Ecosystem | Brought in by / note |
|---|---|---|---|---|
| psycopg, psycopg-binary | 3.3.6 | LGPL-3.0-only | Python | PostgreSQL driver used by the API service; used unmodified as a library. |
| @img/sharp-libvips-linux-x64, @img/sharp-libvips-linuxmusl-x64 | 1.3.4 | LGPL-3.0-or-later | npm (runtime) | Native image library pulled in by Next.js (sharp); used unmodified. |
| pikepdf | 10.17.0 | MPL-2.0 | Python | Used by the scan fallback package (`packages/ocr`) to inspect PDFs; used unmodified. |
| certifi | 2026.10.23 | MPL-2.0 | Python | CA bundle, transitive. |
| pathspec | 1.1.1 | MPL-2.0 | Python | Transitive dependency. |
| axe-core | 4.14.0 | MPL-2.0 | npm (development) | Accessibility testing only. |
| lightningcss, lightningcss-linux-x64-gnu, lightningcss-linux-x64-musl | 1.33.0 | MPL-2.0 | npm (development) | Build tooling only. |
| pypdfium2 | 5.14.0 | BSD-3-Clause, Apache-2.0 and bundled-dependency licences | Python | Metadata lists several licences; see the package for the full set. [VERIFY] |
| satya-affidavit, satya-api, satya-blindgen, satya-forensics, satya-ocr, satya-shared-types, satya-worker | 0.1.0 | UNKNOWN (no licence field in the package's own `pyproject.toml`) | Python | These are this repository's own workspace packages, covered by the repository's Apache-2.0 licence. Adding a licence field is an optional follow-up. |

## Fonts

The workbench bundles self-hosted fonts from the `@fontsource` packages, all under the SIL Open Font License 1.1 (OFL-1.1): `@fontsource/noto-sans`, `@fontsource/noto-sans-devanagari`, `@fontsource/noto-sans-mono`, `@fontsource/public-sans` (all 5.3.0).

## OCR engine and model weights

The optional OCR engine (PaddleOCR, PaddlePaddle and PaddleX) is installed only when the image is built with `WITH_OCR=1` and is not part of the lockfile. `packages/ocr/requirements-ocr.txt` records their licences as Apache-2.0 (paddleocr 3.7.0, paddlepaddle 3.3.1, paddlex 3.7.2). [VERIFY: not re-checked when this file was generated]. Model weights are downloaded at image build time and are not committed to this repository. [VERIFY: licence of the downloaded model weights]

## Python packages

109 packages in the environment.

| Package | Version | Licence |
|---|---|---|
| aiohappyeyeballs | 2.7.1 | Python Software Foundation License |
| aiohttp | 3.14.5 | Apache-2.0 AND MIT |
| aiosignal | 1.4.0 | Apache Software License |
| alembic | 1.20.1 | MIT |
| amqp | 5.4.1 | BSD License |
| annotated-doc | 0.0.5 | MIT |
| annotated-types | 0.8.0 | MIT |
| anyio | 4.15.1 | MIT |
| argcomplete | 3.7.2 | Apache Software License |
| asn1crypto | 1.5.1 | MIT License |
| ast_serialize | 0.13.1 | MIT |
| attrs | 26.1.0 | MIT |
| billiard | 4.3.1 | BSD License |
| black | 26.10.1 | MIT |
| celery | 5.6.3 | BSD-3-Clause |
| certifi | 2026.10.23 | Mozilla Public License 2.0 (MPL 2.0) |
| cffi | 2.1.1 | MIT-0 |
| charset-normalizer | 3.5.2 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| click-didyoumean | 0.3.1 | MIT License |
| click-plugins | 1.1.1.2 | BSD License |
| click-repl | 0.4.1 | MIT |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause |
| datamodel-code-generator | 0.86.0 | MIT |
| fastapi | 0.162.0 | MIT |
| frozenlist | 1.8.0 | Apache-2.0 |
| genson | 1.4.0 | MIT License |
| greenlet | 3.5.6 | MIT AND PSF-2.0 |
| h11 | 0.16.0 | MIT License |
| httpcore | 1.0.9 | BSD-3-Clause |
| httptools | 0.9.0 | MIT |
| httpx | 0.28.1 | BSD License |
| idna | 3.20 | BSD-3-Clause |
| inflect | 7.6.0 | MIT |
| iniconfig | 2.3.1 | MIT |
| isort | 8.0.1 | MIT |
| jaraco.functools | 4.6.0 | MIT |
| Jinja2 | 3.1.6 | BSD License |
| jsonschema | 4.26.0 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| kombu | 5.6.2 | BSD-3-Clause |
| librt | 0.16.0 | MIT |
| lxml | 6.1.3 | BSD-3-Clause |
| Mako | 1.4.3 | MIT |
| MarkupSafe | 3.0.4 | BSD-3-Clause |
| more-itertools | 11.2.1 | MIT |
| multidict | 7.2.1 | Apache-2.0 |
| mypy | 2.4.0 | MIT |
| mypy_extensions | 1.1.0 | MIT |
| opentelemetry-api | 1.45.1 | Apache-2.0 |
| oscrypto | 1.3.0 | MIT License |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pathspec | 1.1.1 | Mozilla Public License 2.0 (MPL 2.0) |
| pdfminer.six | 20260107 | MIT |
| pdfplumber | 0.11.10 | MIT License |
| pikepdf | 10.17.0 | MPL-2.0 |
| pillow | 13.0.0 | MIT-CMU |
| platformdirs | 4.13.5 | MIT |
| pluggy | 1.7.0 | MIT License |
| prompt_toolkit | 3.0.53 | BSD License |
| propcache | 0.5.4 | Apache-2.0 |
| psycopg | 3.3.6 | LGPL-3.0-only |
| psycopg-binary | 3.3.6 | LGPL-3.0-only |
| pycparser | 3.12 | BSD-3-Clause |
| pydantic | 2.14.1 | MIT |
| pydantic-settings | 2.16.1 | MIT |
| pydantic_core | 2.50.1 | MIT |
| Pygments | 2.21.0 | BSD-2-Clause |
| pyHanko | 0.38.0 | MIT |
| pyhanko-certvalidator | 0.33.0 | MIT |
| PyJWT | 2.15.1 | MIT |
| pypdfium2 | 5.14.0 | BSD-3-Clause, Apache-2.0, dependency licenses |
| pytest | 9.1.1 | MIT |
| pytest-asyncio | 1.4.1 | Apache-2.0 |
| python-dateutil | 3.0.0 | Apache Software License; BSD License |
| python-dotenv | 1.2.4 | BSD-3-Clause |
| python-ulid | 4.0.1 | MIT |
| pytokens | 0.4.1 | MIT License |
| PyYAML | 6.0.3 | MIT License |
| redis | 6.4.0 | MIT |
| referencing | 0.37.0 | MIT |
| reportlab | 5.0.1 | BSD License |
| rfc3339-validator | 0.1.4 | MIT License |
| rpds-py | 2026.9.1 | MIT |
| ruff | 0.17.2 | MIT |
| satya-affidavit | 0.1.0 | UNKNOWN |
| satya-api | 0.1.0 | UNKNOWN |
| satya-blindgen | 0.1.0 | UNKNOWN |
| satya-forensics | 0.1.0 | UNKNOWN |
| satya-ocr | 0.1.0 | UNKNOWN |
| satya-shared-types | 0.1.0 | UNKNOWN |
| satya-worker | 0.1.0 | UNKNOWN |
| six | 1.17.0 | MIT License |
| SQLAlchemy | 2.1.6 | MIT |
| starlette | 1.10.0 | BSD-3-Clause |
| typeguard | 4.6.0 | MIT |
| types-PyYAML | 6.0.12.20260906 | Apache-2.0 |
| typing-inspection | 0.4.4 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| tzdata | 2026.5 | Apache-2.0 |
| tzlocal | 5.4.5 | MIT |
| uritools | 6.1.3 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |
| uvloop | 0.23.0 | Apache Software License; MIT License |
| vine | 5.1.0 | BSD License |
| watchfiles | 1.3.0 | MIT License |
| wcwidth | 0.9.4 | MIT License |
| websockets | 17.3 | BSD-3-Clause |
| yarl | 1.25.1 | Apache-2.0 |

## npm packages

443 package versions (runtime: 92, development only: 351). `runtime` means the package is in the production dependency tree of an app; `development` means it is used only for building, linting or testing.

| Package | Version | Licence | Used for |
|---|---|---|---|
| @apidevtools/json-schema-ref-parser | 11.9.3 | MIT | development |
| @babel/code-frame | 7.29.7 | MIT | development |
| @babel/compat-data | 7.29.7 | MIT | development |
| @babel/core | 7.29.7 | MIT | development |
| @babel/generator | 7.29.8 | MIT | development |
| @babel/helper-compilation-targets | 7.29.7 | MIT | development |
| @babel/helper-globals | 7.29.7 | MIT | development |
| @babel/helper-module-imports | 7.29.7 | MIT | development |
| @babel/helper-module-transforms | 7.29.7 | MIT | development |
| @babel/helper-string-parser | 7.29.11 | MIT | development |
| @babel/helper-validator-identifier | 7.29.7 | MIT | development |
| @babel/helper-validator-option | 7.29.7 | MIT | development |
| @babel/helpers | 7.29.10 | MIT | development |
| @babel/parser | 7.29.11 | MIT | development |
| @babel/runtime | 7.29.10 | MIT | runtime |
| @babel/template | 7.29.7 | MIT | development |
| @babel/traverse | 7.29.10 | MIT | development |
| @babel/types | 7.29.11 | MIT | development |
| @eloqnt/config | 0.1.1 | MIT | runtime |
| @eloqnt/format-json | 0.1.0 | MIT | runtime |
| @eloqnt/format-po | 0.1.1 | MIT | runtime |
| @eslint-community/eslint-utils | 4.10.1 | MIT | development |
| @eslint-community/eslint-utils | 4.9.1 | MIT | development |
| @eslint-community/regexpp | 4.12.2 | MIT | development |
| @eslint/config-array | 0.21.2 | Apache-2.0 | development |
| @eslint/config-helpers | 0.4.2 | Apache-2.0 | development |
| @eslint/core | 0.17.0 | Apache-2.0 | development |
| @eslint/eslintrc | 3.3.7 | MIT | development |
| @eslint/js | 9.39.5 | MIT | development |
| @eslint/object-schema | 2.1.7 | Apache-2.0 | development |
| @eslint/plugin-kit | 0.4.1 | Apache-2.0 | development |
| @fontsource/noto-sans | 5.3.0 | OFL-1.1 | runtime |
| @fontsource/noto-sans-devanagari | 5.3.0 | OFL-1.1 | runtime |
| @fontsource/noto-sans-mono | 5.3.0 | OFL-1.1 | runtime |
| @fontsource/public-sans | 5.3.0 | OFL-1.1 | runtime |
| @formatjs/fast-memoize | 3.1.7 | MIT | runtime |
| @formatjs/icu-messageformat-parser | 3.5.18 | MIT | runtime |
| @formatjs/icu-messageformat-parser | 3.5.22 | MIT | runtime |
| @formatjs/icu-skeleton-parser | 2.1.11 | MIT | runtime |
| @formatjs/icu-skeleton-parser | 2.1.12 | MIT | runtime |
| @formatjs/intl-localematcher | 0.8.14 | MIT | runtime |
| @humanfs/core | 0.19.2 | Apache-2.0 | development |
| @humanfs/node | 0.16.8 | Apache-2.0 | development |
| @humanfs/types | 0.15.0 | Apache-2.0 | development |
| @humanwhocodes/module-importer | 1.0.1 | Apache-2.0 | development |
| @humanwhocodes/retry | 0.4.3 | Apache-2.0 | development |
| @img/colour | 1.1.0 | MIT | runtime |
| @img/sharp-libvips-linux-x64 | 1.3.4 | LGPL-3.0-or-later | runtime |
| @img/sharp-libvips-linuxmusl-x64 | 1.3.4 | LGPL-3.0-or-later | runtime |
| @img/sharp-linux-x64 | 0.35.5 | Apache-2.0 | runtime |
| @img/sharp-linuxmusl-x64 | 0.35.5 | Apache-2.0 | runtime |
| @internationalized/date | 3.12.4 | Apache-2.0 | runtime |
| @internationalized/number | 3.6.9 | Apache-2.0 | runtime |
| @internationalized/string | 3.2.10 | Apache-2.0 | runtime |
| @jridgewell/gen-mapping | 0.3.13 | MIT | development |
| @jridgewell/remapping | 2.3.5 | MIT | development |
| @jridgewell/resolve-uri | 3.1.2 | MIT | development |
| @jridgewell/sourcemap-codec | 1.6.0 | MIT | development |
| @jridgewell/trace-mapping | 0.3.31 | MIT | development |
| @jsdevtools/ono | 7.1.3 | MIT | development |
| @napi-rs/canvas | 0.1.100 | MIT | runtime |
| @napi-rs/canvas-linux-x64-gnu | 0.1.100 | MIT | runtime |
| @napi-rs/canvas-linux-x64-musl | 0.1.100 | MIT | runtime |
| @next/env | 16.4.3 | MIT | runtime |
| @next/eslint-plugin-next | 16.4.3 | MIT | development |
| @next/swc-linux-x64-gnu | 16.4.3 | MIT | runtime |
| @next/swc-linux-x64-musl | 16.4.3 | MIT | runtime |
| @nodelib/fs.scandir | 2.1.5 | MIT | development |
| @nodelib/fs.stat | 2.0.5 | MIT | development |
| @nodelib/fs.walk | 1.2.8 | MIT | development |
| @nolyfill/is-core-module | 1.0.39 | MIT | development |
| @oxc-project/types | 0.155.0 | MIT | development |
| @panva/hkdf | 1.2.1 | MIT | runtime |
| @parcel/watcher | 2.6.0 | MIT | runtime |
| @parcel/watcher-linux-x64-glibc | 2.6.0 | MIT | runtime |
| @parcel/watcher-linux-x64-musl | 2.6.0 | MIT | runtime |
| @react-types/shared | 3.37.0 | Apache-2.0 | runtime |
| @rolldown/binding-linux-x64-gnu | 1.2.15 | MIT | development |
| @rolldown/binding-linux-x64-musl | 1.2.15 | MIT | development |
| @rolldown/pluginutils | 1.0.1 | MIT | development |
| @rtsao/scc | 1.1.0 | MIT | development |
| @schummar/icu-type-parser | 1.21.5 | MIT | runtime |
| @swc/core | 1.16.20 | Apache-2.0 | runtime |
| @swc/core-linux-x64-gnu | 1.16.20 | Apache-2.0 AND MIT | runtime |
| @swc/core-linux-x64-musl | 1.16.20 | Apache-2.0 AND MIT | runtime |
| @swc/counter | 0.1.3 | Apache-2.0 | runtime |
| @swc/helpers | 0.5.23 | Apache-2.0 | runtime |
| @swc/types | 0.1.28 | Apache-2.0 | runtime |
| @types/chai | 5.2.3 | MIT | development |
| @types/deep-eql | 4.0.2 | MIT | development |
| @types/estree | 1.0.9 | MIT | development |
| @types/json-schema | 7.0.15 | MIT | development |
| @types/json5 | 0.0.29 | MIT | development |
| @types/lodash | 4.17.27 | MIT | development |
| @types/node | 24.19.2 | MIT | runtime |
| @types/react | 19.3.0 | MIT | runtime |
| @types/react-dom | 19.3.0 | MIT | development |
| @typescript-eslint/eslint-plugin | 8.72.0 | MIT | development |
| @typescript-eslint/parser | 8.72.0 | MIT | development |
| @typescript-eslint/project-service | 8.72.0 | MIT | development |
| @typescript-eslint/scope-manager | 8.72.0 | MIT | development |
| @typescript-eslint/tsconfig-utils | 8.72.0 | MIT | development |
| @typescript-eslint/type-utils | 8.72.0 | MIT | development |
| @typescript-eslint/types | 8.72.0 | MIT | development |
| @typescript-eslint/typescript-estree | 8.72.0 | MIT | development |
| @typescript-eslint/utils | 8.72.0 | MIT | development |
| @typescript-eslint/visitor-keys | 8.72.0 | MIT | development |
| @unrs/resolver-binding-linux-x64-gnu | 1.12.2 | MIT | development |
| @unrs/resolver-binding-linux-x64-musl | 1.12.2 | MIT | development |
| @vitest/mocker | 5.0.5 | MIT | development |
| @vitest/spy | 5.0.5 | MIT | development |
| acorn | 8.19.0 | MIT | development |
| acorn-jsx | 5.3.2 | MIT | development |
| ajv | 6.15.0 | MIT | development |
| ajv | 8.20.0 | MIT | development |
| ajv-formats | 3.0.1 | MIT | development |
| ansi-styles | 4.3.0 | MIT | development |
| argparse | 2.0.1 | Python-2.0 | development |
| argparse | 3.0.4 | PSF-2.0 | development |
| aria-hidden | 1.2.6 | MIT | runtime |
| aria-query | 5.3.2 | Apache-2.0 | development |
| array-buffer-byte-length | 1.0.2 | MIT | development |
| array-includes | 3.2.0 | MIT | development |
| array.prototype.findlast | 1.2.5 | MIT | development |
| array.prototype.findlastindex | 1.2.6 | MIT | development |
| array.prototype.flat | 1.3.3 | MIT | development |
| array.prototype.flatmap | 1.3.3 | MIT | development |
| array.prototype.tosorted | 1.1.4 | MIT | development |
| arraybuffer.prototype.slice | 1.0.4 | MIT | development |
| assertion-error | 2.0.1 | MIT | development |
| ast-types-flow | 0.0.8 | MIT | development |
| async-function | 1.0.0 | MIT | development |
| available-typed-arrays | 1.0.7 | MIT | development |
| axe-core | 4.14.0 | MPL-2.0 | development |
| axobject-query | 4.1.0 | Apache-2.0 | development |
| balanced-match | 1.0.2 | MIT | development |
| balanced-match | 4.0.4 | MIT | development |
| baseline-browser-mapping | 2.11.33 | Apache-2.0 | runtime |
| brace-expansion | 1.1.21 | MIT | development |
| brace-expansion | 5.0.12 | MIT | development |
| braces | 3.0.3 | MIT | development |
| browserslist | 4.29.4 | MIT | development |
| call-bind | 1.0.9 | MIT | development |
| call-bind-apply-helpers | 1.0.2 | MIT | development |
| call-bound | 1.0.4 | MIT | development |
| callsites | 3.1.0 | MIT | development |
| caniuse-lite | 1.0.30001819 | CC-BY-4.0 | runtime |
| chai | 6.3.0 | MIT | development |
| chalk | 4.1.2 | MIT | development |
| client-only | 0.0.1 | MIT | runtime |
| clsx | 2.1.1 | MIT | runtime |
| color-convert | 2.0.1 | MIT | development |
| color-name | 1.1.4 | MIT | development |
| concat-map | 0.0.1 | MIT | development |
| content-type | 2.1.0 | MIT | runtime |
| convert-source-map | 2.0.0 | MIT | development |
| cookie | 0.7.2 | MIT | runtime |
| cross-spawn | 7.0.6 | MIT | development |
| csstype | 3.2.3 | MIT | runtime |
| damerau-levenshtein | 1.0.8 | BSD-2-Clause | development |
| data-view-buffer | 1.0.2 | MIT | development |
| data-view-byte-length | 1.0.2 | MIT | development |
| data-view-byte-offset | 1.0.1 | MIT | development |
| debug | 3.2.7 | MIT | development |
| debug | 4.4.3 | MIT | development |
| deep-is | 0.1.4 | MIT | development |
| define-data-property | 1.1.4 | MIT | development |
| define-properties | 1.2.1 | MIT | development |
| detect-libc | 2.1.2 | Apache-2.0 | runtime |
| doctrine | 2.1.0 | Apache-2.0 | development |
| dunder-proto | 1.0.1 | MIT | development |
| electron-to-chromium | 1.5.464 | ISC | development |
| emoji-regex | 9.2.2 | MIT | development |
| es-abstract | 1.24.2 | MIT | development |
| es-abstract-get | 1.0.0 | MIT | development |
| es-define-property | 1.0.1 | MIT | development |
| es-errors | 1.3.0 | MIT | development |
| es-iterator-helpers | 1.4.0 | MIT | development |
| es-module-lexer | 2.3.2 | MIT | development |
| es-object-atoms | 1.1.2 | MIT | development |
| es-set-tostringtag | 2.1.0 | MIT | development |
| es-shim-unscopables | 1.1.0 | MIT | development |
| es-to-primitive | 1.3.4 | MIT | development |
| escalade | 3.2.0 | MIT | development |
| escape-string-regexp | 4.0.0 | MIT | development |
| eslint | 9.39.5 | MIT | development |
| eslint-config-next | 16.4.3 | MIT | development |
| eslint-import-resolver-node | 0.3.10 | MIT | development |
| eslint-import-resolver-typescript | 3.10.1 | ISC | development |
| eslint-module-utils | 2.14.0 | MIT | development |
| eslint-plugin-import | 2.32.0 | MIT | development |
| eslint-plugin-jsx-a11y | 6.10.2 | MIT | development |
| eslint-plugin-react | 7.37.5 | MIT | development |
| eslint-plugin-react-hooks | 7.1.1 | MIT | development |
| eslint-scope | 8.4.0 | BSD-2-Clause | development |
| eslint-visitor-keys | 3.4.3 | Apache-2.0 | development |
| eslint-visitor-keys | 4.2.1 | Apache-2.0 | development |
| eslint-visitor-keys | 5.0.1 | Apache-2.0 | development |
| espree | 10.4.0 | BSD-2-Clause | development |
| esquery | 1.7.0 | BSD-3-Clause | development |
| esrecurse | 4.3.0 | BSD-2-Clause | development |
| estraverse | 5.3.0 | BSD-2-Clause | development |
| estree-walker | 3.0.3 | MIT | development |
| esutils | 2.0.3 | BSD-2-Clause | development |
| expect-type | 1.4.0 | Apache-2.0 | development |
| fast-deep-equal | 3.1.3 | MIT | development |
| fast-glob | 3.3.1 | MIT | development |
| fast-json-stable-stringify | 2.1.0 | MIT | development |
| fast-levenshtein | 2.0.6 | MIT | development |
| fast-uri | 3.1.9 | BSD-3-Clause | development |
| fastq | 1.20.3 | ISC | development |
| fdir | 6.5.0 | MIT | development |
| file-entry-cache | 8.0.0 | MIT | development |
| fill-range | 7.1.1 | MIT | development |
| find-up | 5.0.0 | MIT | development |
| flat-cache | 4.0.1 | MIT | development |
| flatted | 3.4.4 | ISC | development |
| for-each | 0.3.5 | MIT | development |
| function-bind | 1.1.2 | MIT | development |
| function.prototype.name | 1.2.0 | MIT | development |
| functions-have-names | 1.2.3 | MIT | development |
| generator-function | 2.0.1 | MIT | development |
| gensync | 1.0.0-beta.2 | MIT | development |
| get-intrinsic | 1.3.0 | MIT | development |
| get-proto | 1.0.1 | MIT | development |
| get-symbol-description | 1.1.0 | MIT | development |
| get-tsconfig | 4.14.3 | MIT | development |
| glob-parent | 5.1.2 | ISC | development |
| glob-parent | 6.0.2 | ISC | development |
| globals | 14.0.0 | MIT | development |
| globals | 16.4.0 | MIT | development |
| globalthis | 1.0.4 | MIT | development |
| gopd | 1.2.0 | MIT | development |
| has-bigints | 1.1.0 | MIT | development |
| has-flag | 4.0.0 | MIT | development |
| has-property-descriptors | 1.0.2 | MIT | development |
| has-proto | 1.2.0 | MIT | development |
| has-symbols | 1.1.0 | MIT | development |
| has-tostringtag | 1.0.2 | MIT | development |
| hasown | 2.0.4 | MIT | development |
| hermes-estree | 0.25.1 | MIT | development |
| hermes-parser | 0.25.1 | MIT | development |
| icu-minify | 4.14.9 | MIT | runtime |
| ignore | 5.3.2 | MIT | development |
| ignore | 7.0.14 | MIT | development |
| import-fresh | 3.3.1 | MIT | development |
| imurmurhash | 0.1.4 | MIT | development |
| internal-slot | 1.1.0 | MIT | development |
| intl-messageformat | 11.2.15 | BSD-3-Clause | runtime |
| is-array-buffer | 3.0.5 | MIT | development |
| is-async-function | 2.1.1 | MIT | development |
| is-bigint | 1.1.0 | MIT | development |
| is-boolean-object | 1.2.2 | MIT | development |
| is-bun-module | 2.0.0 | MIT | development |
| is-callable | 1.2.7 | MIT | development |
| is-core-module | 2.17.0 | MIT | development |
| is-data-view | 1.0.2 | MIT | development |
| is-date-object | 1.1.0 | MIT | development |
| is-document.all | 1.0.0 | MIT | development |
| is-extglob | 2.1.1 | MIT | runtime |
| is-finalizationregistry | 1.1.1 | MIT | development |
| is-generator-function | 1.1.2 | MIT | development |
| is-glob | 4.0.3 | MIT | runtime |
| is-map | 2.0.3 | MIT | development |
| is-negative-zero | 2.0.3 | MIT | development |
| is-number | 7.0.0 | MIT | development |
| is-number-object | 1.1.1 | MIT | development |
| is-regex | 1.2.1 | MIT | development |
| is-set | 2.0.3 | MIT | development |
| is-shared-array-buffer | 1.0.4 | MIT | development |
| is-string | 1.1.1 | MIT | development |
| is-symbol | 1.1.1 | MIT | development |
| is-typed-array | 1.1.15 | MIT | development |
| is-weakmap | 2.0.2 | MIT | development |
| is-weakref | 1.1.1 | MIT | development |
| is-weakset | 2.0.4 | MIT | development |
| isarray | 2.0.5 | MIT | development |
| isexe | 2.0.0 | ISC | development |
| iterator.prototype | 1.1.5 | MIT | development |
| jose | 4.15.9 | MIT | runtime |
| js-tokens | 4.0.0 | MIT | development |
| js-yaml | 4.3.2 | MIT | development |
| js-yaml | 5.5.0 | MIT | development |
| jsesc | 3.1.0 | MIT | development |
| json-buffer | 3.0.1 | MIT | development |
| json-schema-to-typescript | 16.0.0 | MIT | development |
| json-schema-traverse | 0.4.1 | MIT | development |
| json-schema-traverse | 1.0.0 | MIT | development |
| json-stable-stringify-without-jsonify | 1.0.1 | MIT | development |
| json5 | 1.0.2 | MIT | development |
| json5 | 2.2.3 | MIT | development |
| jsx-ast-utils | 3.3.5 | MIT | development |
| keyv | 4.5.4 | MIT | development |
| language-subtag-registry | 0.3.23 | CC0-1.0 | development |
| language-tags | 1.0.9 | MIT | development |
| levn | 0.4.1 | MIT | development |
| lightningcss | 1.33.0 | MPL-2.0 | development |
| lightningcss-linux-x64-gnu | 1.33.0 | MPL-2.0 | development |
| lightningcss-linux-x64-musl | 1.33.0 | MPL-2.0 | development |
| locate-path | 6.0.0 | MIT | development |
| lodash | 4.18.1 | MIT | development |
| lodash.merge | 4.6.2 | MIT | development |
| loose-envify | 1.4.0 | MIT | development |
| lru-cache | 5.1.1 | ISC | development |
| lru-cache | 6.0.0 | ISC | runtime |
| magic-string | 1.4.3 | MIT | development |
| math-intrinsics | 1.1.0 | MIT | development |
| merge2 | 1.4.1 | MIT | development |
| micromatch | 4.0.8 | MIT | development |
| minimatch | 10.2.6 | BlueOak-1.0.0 | development |
| minimatch | 3.1.5 | ISC | development |
| minimist | 1.2.8 | MIT | development |
| ms | 2.1.3 | MIT | development |
| nanoid | 3.3.20 | MIT | runtime |
| napi-postinstall | 0.3.7 | MIT | development |
| natural-compare | 1.4.0 | MIT | development |
| negotiator | 1.1.0 | MIT | runtime |
| next | 16.4.3 | MIT | runtime |
| next-auth | 4.24.15 | ISC | runtime |
| next-intl | 4.14.9 | MIT | runtime |
| next-intl-swc-plugin-extractor | 4.14.9 | MIT | runtime |
| node-addon-api | 7.1.1 | MIT | runtime |
| node-exports-info | 1.6.2 | MIT | development |
| node-releases | 2.0.60 | MIT | development |
| oauth | 0.9.15 | MIT | runtime |
| object-assign | 4.1.1 | MIT | development |
| object-hash | 2.2.0 | MIT | runtime |
| object-inspect | 1.13.4 | MIT | development |
| object-keys | 1.1.1 | MIT | development |
| object.assign | 4.1.7 | MIT | development |
| object.entries | 1.1.9 | MIT | development |
| object.fromentries | 2.0.8 | MIT | development |
| object.groupby | 1.0.3 | MIT | development |
| object.values | 1.2.1 | MIT | development |
| obug | 3.0.0 | MIT | development |
| oidc-token-hash | 5.2.0 | MIT | runtime |
| openid-client | 5.7.1 | MIT | runtime |
| optionator | 0.9.4 | MIT | development |
| own-keys | 1.0.2 | MIT | development |
| p-limit | 3.1.0 | MIT | development |
| p-locate | 5.0.0 | MIT | development |
| parent-module | 1.0.1 | MIT | development |
| path-exists | 4.0.0 | MIT | development |
| path-key | 3.1.1 | MIT | development |
| path-parse | 1.0.7 | MIT | development |
| pdfjs-dist | 5.7.284 | Apache-2.0 | runtime |
| picocolors | 1.1.1 | ISC | runtime |
| picomatch | 2.3.2 | MIT | development |
| picomatch | 4.0.7 | MIT | runtime |
| po-parser | 2.2.0 | MIT | runtime |
| possible-typed-array-names | 1.1.0 | MIT | development |
| postcss | 8.5.23 | MIT | runtime |
| postcss | 8.5.31 | MIT | development |
| preact | 10.29.8 | MIT | runtime |
| preact-render-to-string | 5.2.6 | MIT | runtime |
| prelude-ls | 1.2.1 | MIT | development |
| prettier | 3.9.10 | MIT | development |
| pretty-format | 3.8.0 | MIT | runtime |
| prop-types | 15.8.1 | MIT | development |
| punycode | 2.3.1 | MIT | development |
| queue-microtask | 1.2.3 | MIT | development |
| react | 19.3.1 | MIT | runtime |
| react-aria | 3.53.1 | Apache-2.0 | runtime |
| react-aria-components | 1.22.1 | Apache-2.0 | runtime |
| react-dom | 19.3.1 | MIT | runtime |
| react-is | 16.13.1 | MIT | development |
| react-stately | 3.51.0 | Apache-2.0 | runtime |
| reflect.getprototypeof | 1.0.10 | MIT | development |
| regexp.prototype.flags | 1.5.4 | MIT | development |
| require-from-string | 2.0.2 | MIT | development |
| resolve | 2.0.0-next.7 | MIT | development |
| resolve-from | 4.0.0 | MIT | development |
| resolve-pkg-maps | 1.0.0 | MIT | development |
| reusify | 1.1.0 | MIT | development |
| rolldown | 1.2.15 | MIT | development |
| run-parallel | 1.2.0 | MIT | development |
| safe-array-concat | 1.1.4 | MIT | development |
| safe-push-apply | 1.0.0 | MIT | development |
| safe-regex-test | 1.1.0 | MIT | development |
| scheduler | 0.28.0 | MIT | runtime |
| semver | 6.3.1 | ISC | development |
| semver | 7.8.5 | ISC | runtime |
| set-function-length | 1.2.2 | MIT | development |
| set-function-name | 2.0.2 | MIT | development |
| set-proto | 1.0.0 | MIT | development |
| sharp | 0.35.5 | Apache-2.0 | runtime |
| shebang-command | 2.0.0 | MIT | development |
| shebang-regex | 3.0.0 | MIT | development |
| side-channel | 1.1.1 | MIT | development |
| side-channel-list | 1.0.1 | MIT | development |
| side-channel-map | 1.0.1 | MIT | development |
| side-channel-weakmap | 1.0.2 | MIT | development |
| source-map-js | 1.2.2 | BSD-3-Clause | runtime |
| stable-hash | 0.0.5 | MIT | development |
| std-env | 4.3.0 | MIT | development |
| stop-iteration-iterator | 1.1.0 | MIT | development |
| string.prototype.includes | 2.0.1 | MIT | development |
| string.prototype.matchall | 4.1.0 | MIT | development |
| string.prototype.repeat | 1.0.0 | MIT | development |
| string.prototype.trim | 1.2.11 | MIT | development |
| string.prototype.trimend | 1.0.10 | MIT | development |
| string.prototype.trimstart | 1.0.8 | MIT | development |
| strip-bom | 3.0.0 | MIT | development |
| strip-json-comments | 3.1.1 | MIT | development |
| styled-jsx | 5.1.6 | MIT | runtime |
| supports-color | 7.2.0 | MIT | development |
| supports-preserve-symlinks-flag | 1.0.0 | MIT | development |
| tinybench | 6.2.2 | MIT | development |
| tinyexec | 1.3.1 | MIT | development |
| tinyglobby | 0.2.17 | MIT | development |
| to-regex-range | 5.0.1 | MIT | development |
| ts-api-utils | 2.5.0 | MIT | development |
| tsconfig-paths | 3.15.0 | MIT | development |
| tslib | 2.8.1 | 0BSD | runtime |
| type-check | 0.4.0 | MIT | development |
| typed-array-buffer | 1.0.3 | MIT | development |
| typed-array-byte-length | 1.0.3 | MIT | development |
| typed-array-byte-offset | 1.0.5 | MIT | development |
| typed-array-length | 1.0.8 | MIT | development |
| typescript | 6.0.3 | Apache-2.0 | development |
| typescript-eslint | 8.72.0 | MIT | development |
| unbox-primitive | 1.1.0 | MIT | development |
| undici-types | 7.24.6 | MIT | runtime |
| unrs-resolver | 1.12.2 | MIT | development |
| update-browserslist-db | 1.3.4 | MIT | development |
| uri-js | 4.4.1 | BSD-2-Clause | development |
| use-intl | 4.14.9 | MIT | runtime |
| use-sync-external-store | 1.7.0 | MIT | runtime |
| uuid | 11.1.1 | MIT | runtime |
| vite | 8.3.5 | MIT | development |
| vitest | 5.0.5 | MIT | development |
| which | 2.0.2 | ISC | development |
| which-boxed-primitive | 1.1.1 | MIT | development |
| which-builtin-type | 1.2.1 | MIT | development |
| which-collection | 1.0.2 | MIT | development |
| which-typed-array | 1.1.24 | MIT | development |
| why-is-node-running | 3.2.1 | MIT | development |
| word-wrap | 1.2.5 | MIT | development |
| yallist | 3.1.1 | ISC | development |
| yallist | 4.0.0 | ISC | runtime |
| yocto-queue | 0.1.0 | MIT | development |
| zod | 4.6.7 | MIT | development |
| zod-validation-error | 4.0.2 | MIT | development |
