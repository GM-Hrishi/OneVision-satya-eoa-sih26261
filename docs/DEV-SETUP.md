# Developer setup
SATYA-EoA runs as one Docker Compose stack (8 services plus two one-shot jobs) within an 8 GB memory budget. Synthetic data only: never copy anything from `data/real-samples/` (git-ignored) into the repo, a cloud session, a log or an issue.

After setup, the URLs are:

| URL | What |
|---|---|
| https://localhost | SATYA workbench (sign in as `rb.southern.demo`) |
| https://localhost/api/v1/health | Gateway health (Postgres, Valkey, Keycloak) |
| https://portal.localhost | Approval Portal (Mock, for demo) |
| https://auth.localhost | Keycloak sign-in pages (admin console is not exposed) |

The demo password for every synthetic user is in `.env` (`grep DEMO_USER_PASSWORD .env`).

## Windows 11 + WSL2 (recommended path on the team laptops)
1. **Install Docker Desktop** and, in *Settings → General*, keep *Use the WSL 2 based engine* on. In *Settings → Resources → WSL integration*, enable your Ubuntu distribution.
2. **Install a WSL distribution** (PowerShell as administrator): `wsl --install -d Ubuntu`, then reboot and create your Linux user.
3. **Give WSL enough memory.** Create `%UserProfile%\.wslconfig` (for example `C:\Users\<you>\.wslconfig`):
   ```ini
   [wsl2]
   memory=10GB
   processors=6
   ```
   Then run `wsl --shutdown` in PowerShell and restart Docker Desktop. The stack's limits add up to 5.6 GB; 10 GB leaves room for builds.
4. **Clone inside the WSL filesystem**, not under `/mnt/c` (bind mounts and builds are many times faster there):
   ```bash
   cd ~ && git clone <repository-url> satya-eoa && cd satya-eoa
   sudo apt-get update && sudo apt-get install -y make python3
   ```
5. **Start it**:
   ```bash
   make secrets   # writes .env with random secrets (git-ignored)
   make up        # builds, starts and waits until every service is healthy (first run ~5-10 min)
   ```
6. **Trust Caddy's local CA once** so browsers show HTTPS without warnings:
   ```bash
   make trust-ca                                   # writes infra/caddy/local-root.crt (git-ignored)
   cp infra/caddy/local-root.crt /mnt/c/Users/<you>/Downloads/satya-local-root.crt
   ```
   In Windows: double-click `satya-local-root.crt` → *Install Certificate* → *Current User* → *Place all certificates in the following store* → **Trusted Root Certification Authorities** → Finish. (Or in PowerShell: `certutil -addstore -user Root $HOME\Downloads\satya-local-root.crt`.) Chrome and Edge use the Windows store. **Firefox:** *Settings → Privacy & Security → Certificates → View Certificates → Authorities → Import*, tick "Trust this CA to identify websites".
   This trusts a CA that exists only on your machine; nothing in the browser's security settings is changed. Remove it with `certmgr.msc` when you stop working on the project.
7. Open https://localhost and sign in as `rb.southern.demo`.

**Without WSL** (not recommended): from PowerShell 7 in the repo folder, run `pwsh infra/scripts/up.ps1`. It generates `.env` and starts the stack, but the `make` targets (smoke tests, ledger check, reset) need WSL or Git Bash.

## Linux
Install Docker Engine with the Compose plugin, `make`, `python3`, then:
```bash
make secrets && make up && make trust-ca
sudo cp infra/caddy/local-root.crt /usr/local/share/ca-certificates/satya-local-root.crt && sudo update-ca-certificates
# Chrome/Chromium and Firefox use NSS, not the system store:
sudo apt-get install -y libnss3-tools
certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "SATYA Caddy local root" -i infra/caddy/local-root.crt
```
Ports 80 and 443 must be free. Browsers and curl resolve `*.localhost` to 127.0.0.1 on their own; other tools may not (the test scripts handle it).

## macOS
Docker Desktop (give it 10 GB memory in *Settings → Resources*), then:
```bash
make secrets && make up && make trust-ca
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain infra/caddy/local-root.crt
```
Firefox: import the CA in its own certificate settings as on Windows.

## Everyday commands
| Command | What it does |
|---|---|
| `make up` / `make down` | start (and wait for health) / stop, keeping data |
| `make ps` · `make logs SERVICE=api` | status · follow logs |
| `make reset` | stop and **delete all volumes** (asks you to type `reset`) |
| `make install` | install JS + Python deps for local development |
| `make lint` · `make typecheck` · `make test` | the same checks CI runs (no stack needed) |
| `make test-db` | Postgres-backed API tests in a throwaway container |
| `make smoke` · `make e2e` | stack smoke tests · browser acceptance (needs Playwright) |
| `make ledger-verify` | recompute the hash-chained ledger |
| `make gen-types` | regenerate TS/Pydantic contracts after a schema change |
| `make guard` · `make secret-scan` | real-data guard · gitleaks |
| `make mem-check` | memory limits present and ≤ 8 GB in total |

Regenerated secrets (`FORCE=1 make secrets`) only take effect for Postgres and Keycloak after `make reset`, because both keep their first-run credentials in their volumes.

## Cloud session note (Claude Code on the web)
The cloud VM is Linux with Docker available, but:
- **The Docker daemon may not be running.** Start it with `sudo dockerd > /tmp/dockerd.log 2>&1 &` and wait for `docker info` to succeed.
- **Outbound HTTPS goes through a TLS-intercepting proxy.** Containers do not trust its CA, so image builds fail to download packages. Generate secrets with the proxy's CA bundle so builds get it as a BuildKit secret (never stored in an image): `SATYA_EXTRA_CA_FILE=/root/.ccr/ca-bundle.crt make secrets`. It is copied to `infra/certs/extra-ca.pem` (git-ignored).
- **Registries:** Docker Hub may answer `429 Too Many Requests` (retry after a minute); `quay.io` and `ghcr.io` blobs were blocked, which is why Keycloak comes from Docker Hub and uv is installed from PyPI.
- Containers are lost when the VM is reclaimed; everything needed to rebuild is in git. Run `make up` again.
- Real sample PDFs must never be uploaded to a cloud session.
