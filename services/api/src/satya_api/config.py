"""Gateway settings, read from SATYA_* environment variables (see .env.example, compose)."""

from functools import cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

SUPPORTED_AYS = ("2024-25", "2025-26", "2026-27")
API_VERSION = "v1"
SERVICE_VERSION = "0.1.0"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SATYA_", extra="ignore")

    env: str = "dev"
    database_url: SecretStr = SecretStr("")
    valkey_url: SecretStr = SecretStr("")
    keycloak_url: str = "http://keycloak:8080"
    keycloak_realm: str = "satya"
    # "kid=secret,kid2=secret2". Two kids may be valid at once during rotation (Portal spec §2.2).
    hmac_keys: SecretStr = SecretStr("")
    signature_window_s: int = 300
    dedupe_days: int = 30
    max_body_bytes: int = Field(default=1_048_576, gt=0)
    rate_limit: str = "120/minute"
    client_rate_limit: str = "600/minute"
    cors_origins: str = "https://localhost,https://portal.localhost"
    # Workbench API (OIDC bearer tokens from the workbench client, Portal spec §2.0).
    keycloak_issuer: str = "https://auth.localhost/realms/satya"
    workbench_client_id: str = "satya-web"
    user_rate_limit: str = "300/minute"
    # Gateway tokenisation key (Portal spec §2.6.1; the gateway holds it in the demo).
    tokenisation_key: SecretStr = SecretStr("")
    # Slice 1: synthetic demo cases served read-only (data/synthetic/cases). Empty = no cases.
    demo_cases_dir: str = ""
    # Slice D: where uploaded synthetic PDFs are kept (named by SHA-256) and the upload limits.
    upload_dir: str = ""
    upload_max_bytes: int = Field(default=5 * 1024 * 1024, gt=0)
    upload_rate_limit: str = "20/minute"
    overview_rate_limit: str = "30/minute"
    # B-28 OCR: engine "paddle" (real, needs the WITH_OCR image) or "none"; OCR is expensive, so
    # every upload also counts against a tighter per-user limit. Page, time and confidence limits
    # are read from SATYA_OCR_* by satya_ocr.OcrSettings.
    ocr_engine: str = "paddle"
    ocr_rate_limit: str = "10/minute"
    # Replay (P-11): archived rule packs, one folder per pack id. Empty = packages/rules/archive.
    rules_archive_dir: str = ""
    replay_rate_limit: str = "10/minute"
    # Run the M5/M6 checks of every demo case once at start so the first queue load is fast.
    warm_cache: bool = False

    def hmac_key_map(self) -> dict[str, bytes]:
        keys: dict[str, bytes] = {}
        for pair in self.hmac_keys.get_secret_value().split(","):
            kid, sep, secret = pair.strip().partition("=")
            if sep and kid and len(secret) >= 32:
                keys[kid] = secret.encode()
        return keys

    def token_key(self) -> bytes:
        key = self.tokenisation_key.get_secret_value()
        return key.encode() if len(key) >= 32 else b""

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


def parse_rate(spec: str) -> tuple[int, int]:
    """'120/minute' -> (120, 60)."""
    count, _, unit = spec.partition("/")
    seconds = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}[unit.strip() or "minute"]
    return int(count), seconds


@cache
def get_settings() -> Settings:
    return Settings()
