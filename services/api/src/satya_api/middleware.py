"""ASGI middleware: trace id + access log, body size limit, per-IP rate limit."""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from satya_api.problems import problem_response
from satya_api.ratelimit import RateLimiter

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

access = logging.getLogger("satya.access")
security = logging.getLogger("satya.security")


def client_ip(scope: Scope) -> str:
    client = scope.get("client")
    return str(client[0]) if client else "unknown"


class TraceMiddleware:
    """Assigns a trace_id (echoed as X-Request-ID) and writes one JSON access line per request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        trace_id = uuid.uuid4().hex
        scope.setdefault("state", {})["trace_id"] = trace_id
        start = time.perf_counter()
        status = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message.setdefault("headers", []).append((b"x-request-id", trace_id.encode()))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            access.info(
                "request",
                extra={
                    "trace_id": trace_id,
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "status": status,
                    "duration_ms": round((time.perf_counter() - start) * 1000, 1),
                    "client_ip": client_ip(scope),
                },
            )


class BodyLimitMiddleware:
    """Rejects bodies over max_bytes with 413 PAYLOAD_TOO_LARGE, whether declared or streamed."""

    def __init__(self, app: ASGIApp, max_bytes: int, upload_max_bytes: int | None = None) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.upload_max_bytes = upload_max_bytes or max_bytes

    def limit_for(self, scope: Scope) -> int:
        """Only the document upload route may carry a PDF (Slice D); every other route is small."""
        path = str(scope.get("path", ""))
        if path.startswith("/v1/cases/") and path.endswith("/documents"):
            return self.upload_max_bytes
        return self.max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") in ("GET", "HEAD", "OPTIONS"):
            await self.app(scope, receive, send)
            return
        trace_id = scope.get("state", {}).get("trace_id", "")
        headers = dict(scope.get("headers") or [])
        declared = headers.get(b"content-length")
        limit = self.limit_for(scope)
        if declared is not None and (not declared.isdigit() or int(declared) > limit):
            await self._reject(scope, receive, send, trace_id)
            return
        chunks: list[bytes] = []
        size = 0
        more = True
        while more:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > limit:
                await self._reject(scope, receive, send, trace_id)
                return
            chunks.append(chunk)
            more = message.get("more_body", False)
        body = b"".join(chunks)
        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        await self.app(scope, replay, send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send, trace_id: str) -> None:
        security.warning(
            "body too large",
            extra={"trace_id": trace_id, "path": scope.get("path"), "client_ip": client_ip(scope)},
        )
        response = problem_response(413, "PAYLOAD_TOO_LARGE", trace_id)
        await response(scope, receive, send)


class RateLimitMiddleware:
    """Per-IP limit on every endpoint (the per-client limit is applied after signature checks)."""

    def __init__(self, app: ASGIApp, limiter: RateLimiter) -> None:
        self.app = app
        self.limiter = limiter

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") == "/v1/health/live":
            await self.app(scope, receive, send)
            return
        retry_after = await self.limiter.hit(client_ip(scope))
        if retry_after is not None:
            trace_id = scope.get("state", {}).get("trace_id", "")
            security.warning(
                "rate limited",
                extra={"trace_id": trace_id, "scope": "ip", "client_ip": client_ip(scope)},
            )
            response = problem_response(
                429, "RATE_LIMITED", trace_id, headers={"Retry-After": str(retry_after)}
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)
