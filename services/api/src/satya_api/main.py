"""SATYA-EoA gateway (Portal Integration API, Portal spec §2). Advisory only; synthetic data only.

Slice 0 endpoints: GET /v1/health, GET /v1/health/live, GET /v1/meta, POST /v1/portal-events.
Slice 1 (Workbench API, OIDC bearer): GET /v1/cases, GET /v1/cases/{case_id}/affidavit-diff (M5).
Slice 2: GET /v1/cases/{case_id}/verification (UI §6.4),
GET /v1/cases/{case_id}/documents/{doc_id}/verification (Portal §2.7) and the M6 sections of the
affidavit diff (same auth, role, region and quota rules).
"""

import asyncio
import hashlib
import json
import logging
import re
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from starlette.exceptions import HTTPException as StarletteHTTPException

from satya_affidavit.engine import ENGINE_VERSION as M5_ENGINE_VERSION
from satya_affidavit.rules import load_ruleset
from satya_api.auth import Principal, TokenVerifier, http_jwks_fetcher
from satya_api.cases import CASE_ID, DOC_ID, CaseError, CaseRepository, FixtureCaseRepository
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
from satya_api.replay import Replayer
from satya_api.rulepacks import RulePackCatalog
from satya_api.signature import HEADER, verify
from satya_api.store import EventStore, InboundEvent, PostgresStore
from satya_api.workflow import FLAG_ID, QUEUE_DIRS, QUEUE_SORTS, Workflow, WorkflowError
from satya_forensics.engine import ENGINE_VERSION as M6_ENGINE_VERSION
from satya_forensics.rules import load_ruleset as load_m6_ruleset
from satya_ocr import OcrSettings
from satya_ocr.engine import PaddleOcrEngine
from satya_shared_types import constants, validator

log = logging.getLogger("satya.api")
security = logging.getLogger("satya.security")

CheckFn = Callable[[], Awaitable[None]]
MAX_REPORTED_ERRORS = 20
RISK_BANDS = ("high", "medium", "low")
REGION_NAME = re.compile(r"[a-z][a-z_]{1,19}")


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
    cases: CaseRepository | None = None,
    verifier: TokenVerifier | None = None,
) -> FastAPI:
    """Build the app. Tests inject a MemoryStore, no Redis, fake checks, cases and a verifier."""
    settings = settings or get_settings()
    configure_logging()
    if redis is None and store is None and settings.valkey_url.get_secret_value():
        redis = Redis.from_url(settings.valkey_url.get_secret_value(), socket_timeout=2)
    ip_limit, ip_window = parse_rate(settings.rate_limit)
    client_limit, client_window = parse_rate(settings.client_rate_limit)
    ip_limiter = RateLimiter(redis, ip_limit, ip_window, "ip")
    client_limiter = RateLimiter(redis, client_limit, client_window, "client")
    user_limit, user_window = parse_rate(settings.user_rate_limit)
    user_limiter = RateLimiter(redis, user_limit, user_window, "user")
    upload_limit, upload_window = parse_rate(settings.upload_rate_limit)
    upload_limiter = RateLimiter(redis, upload_limit, upload_window, "upload")
    ocr_limit, ocr_window = parse_rate(settings.ocr_rate_limit)
    ocr_limiter = RateLimiter(redis, ocr_limit, ocr_window, "ocr")
    overview_limit, overview_window = parse_rate(settings.overview_rate_limit)
    overview_limiter = RateLimiter(redis, overview_limit, overview_window, "overview")
    replay_limit, replay_window = parse_rate(settings.replay_rate_limit)
    replay_limiter = RateLimiter(redis, replay_limit, replay_window, "replay")
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
        realm = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
        app.state.verifier = verifier or TokenVerifier(
            settings.keycloak_issuer,
            settings.workbench_client_id,
            http_jwks_fetcher(app.state.http, f"{realm}/protocol/openid-connect/certs"),
        )
        if cases is not None:
            app.state.cases = cases
        else:
            if not settings.token_key():
                log.error("no tokenisation key (>= 32 chars); land tables cannot be reconciled")
            root = Path(settings.demo_cases_dir) if settings.demo_cases_dir else None
            engine = PaddleOcrEngine() if settings.ocr_engine == "paddle" else None
            app.state.cases = FixtureCaseRepository(
                root,
                settings.token_key(),
                ocr_engine=engine,
                ocr_settings=OcrSettings.from_env(),
                ocr_cache_dir=Path(settings.upload_dir) / "_ocr" if settings.upload_dir else None,
            )
        app.state.workflow = Workflow(
            app.state.cases,
            app.state.store,
            Path(settings.upload_dir) if settings.upload_dir else None,
        )
        await app.state.workflow.restore_uploads()
        app.state.replayer = (
            Replayer(
                app.state.cases,
                app.state.store,
                Path(settings.upload_dir) if settings.upload_dir else None,
                RulePackCatalog(
                    Path(settings.rules_archive_dir) if settings.rules_archive_dir else None
                ),
            )
            if isinstance(app.state.cases, FixtureCaseRepository)
            else None
        )
        warm_task = asyncio.create_task(app.state.workflow.warm()) if settings.warm_cache else None
        if not hmac_keys:
            log.error("no HMAC keys configured; every portal event will be rejected")
        yield
        if warm_task is not None:
            warm_task.cancel()
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
    app.add_middleware(
        BodyLimitMiddleware,
        max_bytes=settings.max_body_bytes,
        upload_max_bytes=settings.upload_max_bytes,
    )
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
            "template_profiles": ["aff2-portal-2024-27"],
            "ruleset_versions": [load_ruleset().ref, load_m6_ruleset().ref],
            "engines": {
                "m5-affidavit-diff": M5_ENGINE_VERSION,
                "m6-signatures": M6_ENGINE_VERSION,
            },
            "adapters": [],
            "adapters_note": (
                "Source answers come from offline checks or simulated services. "
                "Every simulated result is tagged as a simulated source."
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

    # ---- Workbench API (UI spec §6) ------------------------------------------------------------
    async def official(request: Request, role: str | tuple[str, ...] = "RB") -> Principal:
        """Verify the bearer token, apply the per-user quota and require the role."""
        verifier: TokenVerifier = request.app.state.verifier
        principal = await verifier.verify(request.headers.get("authorization"))
        retry_after = await user_limiter.hit(principal.subject)
        if retry_after is not None:
            security.warning("rate limited", extra={"trace_id": trace(request), "scope": "user"})
            raise ProblemError(429, "RATE_LIMITED", headers={"Retry-After": str(retry_after)})
        needed = (role,) if isinstance(role, str) else role
        if not principal.roles.intersection(needed):
            security.warning(
                "permission denied",
                extra={"trace_id": trace(request), "sub": principal.subject, "need": list(needed)},
            )
            raise ProblemError(403, "SCOPE_DENIED")
        return principal

    def in_scope(request: Request, principal: Principal, region: str, case_id: str) -> None:
        if not principal.can_see_region(region):
            security.warning(
                "case outside region scope",
                extra={"trace_id": trace(request), "sub": principal.subject, "case_id": case_id},
            )
            raise ProblemError(403, "SCOPE_DENIED")

    @app.get("/v1/cases")
    async def list_cases(
        request: Request, sort: str | None = None, dir: str | None = None
    ) -> JSONResponse:
        """The queue (RB-02): one row per case with its risk band, label counts and status.

        `sort` (application_id | undisposed_flags | submitted_at | last_activity_at) and `dir`
        (asc | desc) order the rows inside each risk band group; the active sort is echoed.
        """
        principal = await official(request)
        if (sort is not None and sort not in QUEUE_SORTS) or (
            dir is not None and dir not in QUEUE_DIRS
        ):
            raise ProblemError(422, "VALIDATION_FAILED")
        flow: Workflow = request.app.state.workflow
        items = await flow.queue(principal.can_see_region, sort, dir)
        body = {
            "items": items,
            "totals": {
                "submitted": len(items),
                "by_band": {b: sum(1 for i in items if i["risk_band"] == b) for b in RISK_BANDS},
                "sources_unavailable": sum(i["manual_tasks"] for i in items),
            },
            "sort": {
                "key": sort or "undisposed_flags",
                "dir": dir or ("asc" if sort else "desc"),
                "default": sort is None,
                "within": "risk_band",
            },
            "advisory": True,
        }
        return JSONResponse(body, headers={"Cache-Control": "no-store"})

    @app.get("/v1/overview")
    async def overview(
        request: Request, ay: str | None = None, region: str | None = None
    ) -> JSONResponse:
        """Overview counts (RB): same role and region scope as the queue, plus a stricter quota.

        `ay` must be a supported academic year (default: the latest) and `region` a lower-case
        region name the official may see (default: everything the official may see).
        """
        principal = await official(request)
        retry_after = await overview_limiter.hit(principal.subject)
        if retry_after is not None:
            security.warning(
                "rate limited", extra={"trace_id": trace(request), "scope": "overview"}
            )
            raise ProblemError(429, "RATE_LIMITED", headers={"Retry-After": str(retry_after)})
        if ay is not None and ay not in SUPPORTED_AYS:
            raise ProblemError(422, "UNSUPPORTED_AY")
        if region is not None:
            if not REGION_NAME.fullmatch(region):
                raise ProblemError(422, "VALIDATION_FAILED")
            if region != "national" and not principal.can_see_region(region):
                security.warning(
                    "overview outside region scope",
                    extra={"trace_id": trace(request), "sub": principal.subject},
                )
                raise ProblemError(403, "SCOPE_DENIED")
            if region == "national" and "national" not in principal.regions:
                raise ProblemError(403, "SCOPE_DENIED")
        scope = region or ("national" if "national" in principal.regions else None)
        body = await flow_of(request).overview(
            principal.can_see_region, ay or SUPPORTED_AYS[-1], region
        )
        if scope is None:
            scope = ",".join(sorted(principal.regions))
        body["region"] = scope
        return JSONResponse(body, headers={"Cache-Control": "no-store"})

    async def scoped_case(request: Request, case_id: str) -> tuple[Principal, CaseRepository]:
        """Bearer + RB role + quota, then the case must exist and be in the official's region."""
        principal = await official(request)
        if not CASE_ID.fullmatch(case_id):
            raise ProblemError(404, "NOT_FOUND")
        repo: CaseRepository = request.app.state.cases
        summary = await repo.get(case_id)
        if summary is None:
            raise ProblemError(404, "NOT_FOUND")
        in_scope(request, principal, summary.regional_office, case_id)
        return principal, repo

    def unusable(request: Request, case_id: str) -> ProblemError:
        log.exception("case unusable", extra={"trace_id": trace(request), "case_id": case_id})
        return ProblemError(500, "INTERNAL_ERROR")

    @app.get("/v1/cases/{case_id}/affidavit-diff")
    async def affidavit_diff(case_id: str, request: Request) -> JSONResponse:
        principal, repo = await scoped_case(request, case_id)
        try:
            diff = await repo.affidavit_diff(case_id)
        except CaseError:
            raise unusable(request, case_id) from None
        log.info(
            "affidavit diff served",
            extra={"trace_id": trace(request), "sub": principal.subject, "case_id": case_id},
        )
        return JSONResponse(diff, headers={"Cache-Control": "no-store"})

    @app.get("/v1/cases/{case_id}/verification")
    async def case_verification(case_id: str, request: Request) -> JSONResponse:
        """RB-06 data (UI spec §6.4): one label per document, two signature badges."""
        principal, _ = await scoped_case(request, case_id)
        try:
            body = await request.app.state.workflow.verification(case_id)
        except CaseError:
            raise unusable(request, case_id) from None
        log.info(
            "case verification served",
            extra={"trace_id": trace(request), "sub": principal.subject, "case_id": case_id},
        )
        return JSONResponse(body, headers={"Cache-Control": "no-store"})

    @app.get("/v1/cases/{case_id}/documents/{doc_id}/verification")
    async def document_verification(case_id: str, doc_id: str, request: Request) -> JSONResponse:
        """VerificationResult of one document (Portal spec §2.7)."""
        principal, _ = await scoped_case(request, case_id)
        if not DOC_ID.fullmatch(doc_id):
            raise ProblemError(404, "NOT_FOUND")
        try:
            body = await request.app.state.workflow.document_verification(case_id, doc_id)
        except CaseError:
            raise unusable(request, case_id) from None
        if body is None:
            raise ProblemError(404, "NOT_FOUND")
        log.info(
            "document verification served",
            extra={
                "trace_id": trace(request),
                "sub": principal.subject,
                "case_id": case_id,
                "doc_id": doc_id,
            },
        )
        return JSONResponse(body, headers={"Cache-Control": "no-store"})

    # ---- Slice D: review, upload, decisions, audit, alerts -------------------------------------
    class DispositionBody(BaseModel):
        action: str = Field(max_length=32)
        reason: str = Field(max_length=4000)

    class PickBody(BaseModel):
        slot: str = Field(max_length=16)
        source_case_id: str = Field(max_length=64)

    def problem(exc: WorkflowError) -> ProblemError:
        status = 404 if exc.code == "FLAG_NOT_FOUND" else 422
        return ProblemError(status, exc.code)

    def flow_of(request: Request) -> Workflow:
        flow: Workflow = request.app.state.workflow
        return flow

    @app.get("/v1/cases/{case_id}/review")
    async def case_review(case_id: str, request: Request) -> JSONResponse:
        """Documents with labels and source responses, flags with why sentences, band, decisions."""
        await scoped_case(request, case_id)
        try:
            body = await flow_of(request).view(case_id)
        except CaseError:
            raise unusable(request, case_id) from None
        return JSONResponse(body, headers={"Cache-Control": "no-store"})

    async def upload_guard(request: Request, principal: Principal) -> None:
        retry_after = await upload_limiter.hit(principal.subject)
        if retry_after is None:
            retry_after = await ocr_limiter.hit(principal.subject)
        if retry_after is not None:
            security.warning("rate limited", extra={"trace_id": trace(request), "scope": "upload"})
            raise ProblemError(429, "RATE_LIMITED", headers={"Retry-After": str(retry_after)})

    @app.post("/v1/cases/{case_id}/documents")
    async def upload_document(
        case_id: str, request: Request, slot: str, filename: str
    ) -> JSONResponse:
        """Add a synthetic PDF to a slot (raw body). PDF only, 5 MB, checked by name and content."""
        principal, _ = await scoped_case(request, case_id)
        await upload_guard(request, principal)
        if (
            request.headers.get("content-type", "").split(";")[0].strip().lower()
            != "application/pdf"
        ):
            raise ProblemError(415, "UNSUPPORTED_MEDIA_TYPE", "The body must be application/pdf.")
        data = await request.body()
        try:
            view = await flow_of(request).upload(
                case_id, slot, filename, data, principal.subject, "upload"
            )
        except WorkflowError as exc:
            security.warning(
                "upload rejected",
                extra={"trace_id": trace(request), "sub": principal.subject, "code": exc.code},
            )
            raise problem(exc) from None
        except CaseError:
            raise unusable(request, case_id) from None
        return JSONResponse(view, status_code=201, headers={"Cache-Control": "no-store"})

    @app.post("/v1/cases/{case_id}/documents/pick")
    async def pick_document(case_id: str, body: PickBody, request: Request) -> JSONResponse:
        """Use a seeded synthetic document of another case in this case's slot."""
        principal, _ = await scoped_case(request, case_id)
        await upload_guard(request, principal)
        if not CASE_ID.fullmatch(body.source_case_id):
            raise ProblemError(404, "NOT_FOUND")
        try:
            view = await flow_of(request).pick(
                case_id, body.slot, body.source_case_id, principal.subject
            )
        except WorkflowError as exc:
            raise problem(exc) from None
        except CaseError:
            raise unusable(request, case_id) from None
        return JSONResponse(view, status_code=201, headers={"Cache-Control": "no-store"})

    @app.get("/v1/cases/{case_id}/documents/{doc_id}/file")
    async def document_file(case_id: str, doc_id: str, request: Request) -> Response:
        """The stored PDF, for the viewer (inline, never sniffed)."""
        principal, repo = await scoped_case(request, case_id)
        if not DOC_ID.fullmatch(doc_id):
            raise ProblemError(404, "NOT_FOUND")
        try:
            _, _, files = await repo.case_files(case_id)  # type: ignore[attr-defined]
        except CaseError:
            raise unusable(request, case_id) from None
        data = files.get(doc_id)
        if data is None:
            raise ProblemError(404, "NOT_FOUND")
        log.info(
            "document served",
            extra={"trace_id": trace(request), "sub": principal.subject, "doc_id": doc_id},
        )
        return Response(
            data,
            media_type="application/pdf",
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Content-Disposition": 'inline; filename="document.pdf"',
            },
        )

    @app.post("/v1/cases/{case_id}/flags/{flag_id}/disposition")
    async def record_disposition(
        case_id: str, flag_id: str, body: DispositionBody, request: Request
    ) -> JSONResponse:
        """One of the five dispositions, reason of 10+ characters. Advisory: no status changes."""
        principal, _ = await scoped_case(request, case_id)
        if not FLAG_ID.fullmatch(flag_id):
            raise ProblemError(404, "NOT_FOUND")
        try:
            result = await flow_of(request).disposition(
                case_id, flag_id, body.action, body.reason, principal.subject, "RB"
            )
        except WorkflowError as exc:
            raise problem(exc) from None
        except CaseError:
            raise unusable(request, case_id) from None
        security.info(
            "disposition recorded",
            extra={
                "trace_id": trace(request),
                "sub": principal.subject,
                "case_id": case_id,
                "action": body.action,
            },
        )
        return JSONResponse(
            {**result, "advisory": True, "regulatory_effect": "none"},
            status_code=201,
            headers={"Cache-Control": "no-store"},
        )

    @app.get("/v1/cases/{case_id}/replay")
    async def case_replay(
        case_id: str, request: Request, rule_version: str | None = None
    ) -> JSONResponse:
        """Re-run the rules on the stored documents and stored source answers (P-11). Read-only
        except for one `case.replay` ledger entry. `rule_version` is a rule pack id from the
        allow-list (default: the pack of the original run)."""
        principal = await official(request, ("RB", "AU"))
        retry_after = await replay_limiter.hit(principal.subject)
        if retry_after is not None:
            security.warning("rate limited", extra={"trace_id": trace(request), "scope": "replay"})
            raise ProblemError(429, "RATE_LIMITED", headers={"Retry-After": str(retry_after)})
        if not CASE_ID.fullmatch(case_id):
            raise ProblemError(404, "NOT_FOUND")
        replayer: Replayer | None = request.app.state.replayer
        summary = await request.app.state.cases.get(case_id)
        if replayer is None or summary is None:
            raise ProblemError(404, "NOT_FOUND")
        if "AU" not in principal.roles:
            in_scope(request, principal, summary.regional_office, case_id)
        if rule_version is not None and (
            len(rule_version) > 80 or rule_version not in replayer.catalog.available()
        ):
            raise ProblemError(422, "RULE_VERSION_UNKNOWN")
        body = await replayer.replay(case_id, rule_version, principal.subject)
        log.info(
            "case replayed",
            extra={
                "trace_id": trace(request),
                "sub": principal.subject,
                "case_id": case_id,
                "reproducible": body["reproducible"],
            },
        )
        return JSONResponse(body, headers={"Cache-Control": "no-store"})

    @app.get("/v1/audit")
    async def audit(request: Request, case_id: str | None = None) -> JSONResponse:
        """The ledger (newest first) with the chain recomputed on every call (AU and RB)."""
        principal = await official(request, ("AU", "RB"))
        if case_id is not None and not CASE_ID.fullmatch(case_id):
            raise ProblemError(404, "NOT_FOUND")
        flow = flow_of(request)
        allowed = await visible_cases(request, principal)
        body = await flow.audit(case_id, allowed)
        return JSONResponse(body, headers={"Cache-Control": "no-store"})

    async def visible_cases(request: Request, principal: Principal) -> Callable[[str | None], bool]:
        if "AU" in principal.roles:
            return lambda _case: True
        ok = {
            c.case_id
            for c in await request.app.state.cases.list_cases()
            if principal.can_see_region(c.regional_office)
        }
        return lambda case: case in ok

    @app.get("/v1/audit/{seq}")
    async def audit_entry(seq: int, request: Request) -> JSONResponse:
        principal = await official(request, ("AU", "RB"))
        entry = await flow_of(request).audit_entry(seq)
        allowed = await visible_cases(request, principal)
        if entry is None or not allowed(entry["case_id"]):
            raise ProblemError(404, "NOT_FOUND")
        return JSONResponse(entry, headers={"Cache-Control": "no-store"})

    @app.get("/v1/alerts")
    async def alerts(request: Request) -> JSONResponse:
        principal = await official(request)
        items = await flow_of(request).alerts(principal.can_see_region)
        return JSONResponse(
            {"items": items, "advisory": True}, headers={"Cache-Control": "no-store"}
        )

    return app


def app() -> FastAPI:
    """Factory for `uvicorn --factory satya_api.main:app`."""
    return create_app()
