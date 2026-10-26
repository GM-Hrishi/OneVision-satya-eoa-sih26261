# SATYA-EoA: start the stack from Windows PowerShell without WSL.
# Recommended path is WSL2 (`make up` inside the WSL filesystem); see docs/DEV-SETUP.md.
# Usage:  pwsh infra/scripts/up.ps1            (generates .env on first run)
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "Docker Desktop is not installed or not on PATH."
}

function New-Hex([int]$bytes) {
  $buf = New-Object byte[] $bytes
  [System.Security.Cryptography.RandomNumberGenerator]::Fill($buf)
  -join ($buf | ForEach-Object { $_.ToString("x2") })
}

if (-not (Test-Path ".env")) {
  $out = foreach ($line in Get-Content ".env.example") {
    if ($line -match '^([A-Z0-9_]+)=CHANGE_ME$') {
      $key = $Matches[1]
      if ($key -eq "DEMO_USER_PASSWORD") { "$key=Demo-$(New-Hex 10)-Z9" } else { "$key=$(New-Hex 32)" }
    } else { $line }
  }
  Set-Content -Path ".env" -Value $out -Encoding utf8NoBOM
  Write-Host "Wrote .env with fresh random secrets (git-ignored)."
}

docker compose --env-file .env -f infra/docker-compose.yml up -d --build
if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }
Write-Host "Started. Check health with: docker compose --env-file .env -f infra/docker-compose.yml ps"
Write-Host "Workbench https://localhost  ·  Mock portal https://portal.localhost  ·  Keycloak https://auth.localhost"
