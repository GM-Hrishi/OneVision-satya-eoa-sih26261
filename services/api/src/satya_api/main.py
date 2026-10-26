"""SATYA-EoA gateway (Portal Integration API, Portal spec §2). Advisory only; synthetic data only.

Slice 0 endpoints: GET /v1/health, GET /v1/health/live, GET /v1/meta, POST /v1/portal-events.
"""

import asyncio
import hashlib
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from starlette.exceptions import HTTPException as StarletteHTTPException

from satya_api.config import (
    API_VERSION,
    SERVICE_VERSION,
    SUPPORTED_AYS,
    Settings,
    get_settings,
    parse_rate,
)
from satya_api.logs import configure_logging
from satya_api.middleware import (
    BodyLimitMiddleware,
    RateLimitMiddleware,
    TraceMiddleware,
    client_ip,
)
from satya_api.problems import ProblemError, problem_response
from satya_api.ratelimit import RateLimiter
from satya_api.signature import HEADER, verify
from satya_api.store import EventStore, InboundEvent, PostgresStore
from satya_shared_types import constants, validator

log = logging.getLogger("satya.api")
security = logging.getLogger("satya.security")

CheckFn = Callable[[], Awaitable[None]]
MAX_REPORTED_ERRORS = 20


def _schema_errors(name: str, data: Any, prefix: str = "") -> list[dict[str, str]]:
    errors = sorted(validator(name).iter_errors(data), key=lambda e: list(e.absolute_path))
    return [
        {
            "path": prefix + "/" + "/".join(str(p) for p in e.absolute_path),
            "code": str(e.validator),
        }
        for e in errors[:MAX_REPORTED_ERRORS]
    ]


def _rejected_paths(snapshot: dict[str, Any]) -> list[str]:
    """Paths of X fields (Portal spec §2.6.1) present in a snapshot, e.g. faculty[].pan."""
    found: list[str] = []
    for rejected in constants.SNAPSHOT_REJECTED_FIELDS:
        nodes: list[Any] = [snapshot]
        for part in rejected.split("."):
            is_list = part.endswith("[]")
            key = part.removesuffix("[]")
            nxt: list[Any] = []
            for node in nodes:
                if isinstance(node, dict) and key in node:
                    value = node[key]
                    nxt.extend(value if is_list and isinstance(value, list) else [value])
            nodes = nxt
        if nodes:
            found.append(rejected)
    return found


def create_app(
    settings: Settings | None = None,
    store: EventStore | None = None,
    redis: Redis | None = None,
    checks: dict[str, CheckFn] | None = None,
) -> FastAPI:
    """Build the app. Tests inject a MemoryStore, no Redis and fake dependency checks."""
    settings = settings or get_settings()
    configure_logging()
    if redis is None and store is None and settings.valkey_url.get_secret_value():
        redis = Redis.from_url(settings.valkey_url.get_secret_value(), socket_timeout=2)
    ip_limit, ip_window = parse_rate(settings.rate_limit)
    client_limit, client_window = parse_rate(settings.client_rate_limit)
    ip_limiter = RateLimiter(redis, ip_limit, ip_window, "ip")
    client_limiter = RateLimiter(redis, client_limit, client_window, "client")
    hmac_keys = settings.hmac_key_map()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if store is None:
            app.state.store = PostgresStore(
                settings.database_url.get_secret_value(), settings.dedupe_days
            )
        else:
            app.state.store = store
        app.state.http = httpx.AsyncClient(timeout=2.0)
        if not hmac_keys:
            log.error("no HMAC keys configured; every portal event will be rejected")
        yield
        await app.state.store.close()
        await app.state.http.aclose()
        if redis is not None:
            await redis.aclose()

    app = FastAPI(
        title="SATYA-EoA gateway",
        version=SERVICE_VERSION,
        docs_url=None,
        redoc_url=None,
        openapi_url="/v1/openapi.json" if settings.env == "dev" else None,
        lifespan=lifespan,
    )

    # Added innermost first: Trace -> CORS -> RateLimit -> BodyLimit -> routes.
    app.add_middleware(BodyLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(RateLimitMiddleware, limiter=ip_limiter)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization", HEADER, "Idempotency-Key"],
        allow_credentials=True,
        max_age=600,
    )
    app.add_middleware(TraceMiddleware)

    def trace(request: Request) -> str:
        return str(getattr(request.state, "trace_id", ""))

    @app.exception_handler(ProblemError)
    async def on_problem(request: Request, exc: ProblemError) -> JSONResponse:
        return problem_response(
            exc.status, exc.code, trace(request), exc.detail, exc.errors, exc.headers
        )

    @app.exception_handler(StarletteHTTPException)
    async def on_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "INTERNAL_ERROR")
        return problem_response(exc.status_code, code, trace(request))

    @app.exception_handler(RequestValidationError)
    async def on_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        return problem_response(400, "VALIDATION_FAILED", trace(request))

    @app.exception_handler(Exception)
    async def on_error(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error", extra={"trace_id": trace(request)})
        return problem_response(500, "INTERNAL_ERROR", trace(request))

    async def check_postgres() -> None:
        await app.state.store.ping()

    async def check_valkey() -> None:
        if redis is None:
            raise RuntimeError("valkey not configured")
        await redis.ping()

    async def check_keycloak() -> None:
        realm = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
        url = f"{realm}/.well-known/openid-configuration"
        response = await app.state.http.get(url)
        response.raise_for_status()

    dependency_checks = checks or {
        "postgres": check_postgres,
        "valkey": check_valkey,
        "keycloak": check_keycloak,
    }

    @app.get("/v1/health/live")
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/health")
    async def health() -> JSONResponse:
        async def run(fn: CheckFn) -> str:
            try:
                await asyncio.wait_for(fn(), timeout=3)
                return "ok"
            except Exception:  # health must report, never raise
                return "fail"

        names = list(dependency_checks)
        results = await asyncio.gather(*(run(dependency_checks[n]) for n in names))
        status = dict(zip(names, results, strict=True))
        healthy = all(r == "ok" for r in results)
        body: dict[str, Any] = {
            "status": "ok" if healthy else "degraded",
            "version": SERVICE_VERSION,
            "checks": status,
            "adapters": [],
        }
        return JSONResponse(body, status_code=200 if healthy else 503)

    @app.get("/v1/meta")
    async def meta() -> dict[str, Any]:
        return {
            "api_version": API_VERSION,
            "service_version": SERVICE_VERSION,
            "schema_version": constants.EVENT_SPEC,
            "supported_ays": list(SUPPORTED_AYS),
            "aph_editions": ["2024-27"],
            "template_profiles": [],
            "ruleset_versions": [],
            "adapters": [],
            "adapters_note": (
                "No source adapters in slice 0. TN Form D and TN fire licence adapters arrive "
                "in mock mode with M7 (P-5); every mock result is labelled MOCK SOURCE."
            ),
            "advisory": True,
            "regulatory_effect": "none",
        }

    @app.post("/v1/portal-events")
    async def portal_events(request: Request) -> JSONResponse:
        trace_id = trace(request)
        content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type != "application/json":
            raise ProblemError(415, "UNSUPPORTED_MEDIA_TYPE")
        body = await request.body()
        try:
            signed = verify(
                request.headers.get(HEADER), body, hmac_keys, settings.signature_window_s
            )
        except ProblemError as exc:
            security.warning(
                "portal event signature rejected",
                extra={
                    "trace_id": trace_id,
                    "code": exc.code,
                    "client_ip": client_ip(request.scope),
                },
            )
            raise
        retry_after = await client_limiter.hit(signed.kid)
        if retry_after is not None:
            security.warning("rate limited", extra={"trace_id": trace_id, "scope": "client"})
            raise ProblemError(429, "RATE_LIMITED", headers={"Retry-After": str(retry_after)})
        try:
            envelope = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProblemError(400, "VALIDATION_FAILED", "Body is not valid JSON.") from None
        if not isinstance(envelope, dict):
            raise ProblemError(400, "VALIDATION_FAILED", "Body must be a JSON object.")
        if envelope.get("spec") != constants.EVENT_SPEC:
            raise ProblemError(400, "SCHEMA_VERSION_UNSUPPORTED")
        if envelope.get("type") not in constants.INBOUND_EVENT_TYPES:
            raise ProblemError(400, "UNSUPPORTED_EVENT_TYPE")
        errors = _schema_errors("EventEnvelope", envelope)
        if errors:
            raise ProblemError(400, "VALIDATION_FAILED", errors=errors)
        if envelope["subject"]["ay"] not in SUPPORTED_AYS:
            raise ProblemError(400, "UNSUPPORTED_AY")
        snapshot = envelope["data"].get("snapshot")
        if isinstance(snapshot, dict):
            rejected = _rejected_paths(snapshot)
            if rejected:
                security.warning(
                    "personal data rejected",
                    extra={"trace_id": trace_id, "fields": rejected, "kid": signed.kid},
                )
                raise ProblemError(
                    403,
                    "PERSONAL_DATA_REJECTED",
                    errors=[{"path": p, "code": "x_field"} for p in rejected],
                )
            errors = _schema_errors("ApplicationSnapshot", snapshot, "/data/snapshot")
            if errors:
                raise ProblemError(400, "VALIDATION_FAILED", errors=errors)
        result = await request.app.state.store.record_inbound(
            InboundEvent(
                event_id=envelope["event_id"],
                event_type=envelope["type"],
                application_id=envelope["subject"]["application_id"],
                ay=envelope["subject"]["ay"],
                sequence=envelope["sequence"],
                producer=envelope["producer"],
                kid=signed.kid,
                payload_sha256=hashlib.sha256(body).hexdigest(),
            )
        )
        log.info(
            "portal event recorded",
            extra={
                "trace_id": trace_id,
                "event_id": envelope["event_id"],
                "type": envelope["type"],
                "kid": signed.kid,
                "receipt_id": result.receipt_id,
                "duplicate": result.duplicate,
                "ledger_seq": result.ledger_seq,
            },
        )
        if result.duplicate:
            return JSONResponse({"duplicate": True, "receipt_id": result.receipt_id}, 200)
        return JSONResponse({"receipt_id": result.receipt_id, "duplicate": False}, 202)

    return app


def app() -> FastAPI:
    """Factory for `uvicorn --factory satya_api.main:app`."""
    return create_app()
