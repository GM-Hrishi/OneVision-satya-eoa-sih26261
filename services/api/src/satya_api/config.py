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

    def hmac_key_map(self) -> dict[str, bytes]:
        keys: dict[str, bytes] = {}
        for pair in self.hmac_keys.get_secret_value().split(","):
            kid, sep, secret = pair.strip().partition("=")
            if sep and kid and len(secret) >= 32:
                keys[kid] = secret.encode()
        return keys

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
