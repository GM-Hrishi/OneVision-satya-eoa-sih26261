# syntax=docker/dockerfile:1.7
# SATYA worker image (Celery + beat). Build context: repository root (uv workspace).
# Optional build secret `extra_ca`: see services/api/Dockerfile.
ARG PYTHON_IMAGE=python:3.13.17-slim-trixie

FROM ${PYTHON_IMAGE} AS builder
ENV PYTHONDONTWRITEBYTECODE=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /src
RUN --mount=type=secret,id=extra_ca,target=/run/secrets/extra_ca \
    sh -c 'if [ -s /run/secrets/extra_ca ]; then export PIP_CERT=/run/secrets/extra_ca; fi; \
           pip install --no-cache-dir uv==0.11.32'
COPY pyproject.toml uv.lock .python-version ./
COPY services/api/pyproject.toml services/api/
COPY services/worker/pyproject.toml services/worker/
COPY packages/shared-types/python/pyproject.toml packages/shared-types/python/
COPY packages/affidavit/pyproject.toml packages/affidavit/
COPY packages/forensics/pyproject.toml packages/forensics/
RUN --mount=type=secret,id=extra_ca,target=/run/secrets/extra_ca \
    --mount=type=cache,target=/root/.cache/uv \
    sh -c 'if [ -s /run/secrets/extra_ca ]; then export SSL_CERT_FILE=/run/secrets/extra_ca; fi; \
           uv sync --frozen --no-dev --no-install-workspace --package satya-worker'
COPY packages/shared-types/python packages/shared-types/python
COPY services/worker services/worker
RUN --mount=type=secret,id=extra_ca,target=/run/secrets/extra_ca \
    --mount=type=cache,target=/root/.cache/uv \
    sh -c 'if [ -s /run/secrets/extra_ca ]; then export SSL_CERT_FILE=/run/secrets/extra_ca; fi; \
           uv sync --frozen --no-dev --no-editable --package satya-worker'

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/app/.venv/bin:$PATH
RUN groupadd --system --gid 10001 satya && useradd --system --uid 10001 --gid satya --no-create-home satya
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
USER satya
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=5 \
  CMD ["sh", "-c", "celery -A satya_worker.app inspect ping -d celery@$HOSTNAME --timeout 10 >/dev/null"]
CMD ["celery", "-A", "satya_worker.app", "worker", "--beat", "--loglevel", "INFO", "--concurrency", "2"]

# Test image for `make smoke`: same venv plus pytest, runs the integration tests on the compose network.
FROM builder AS test-builder
RUN --mount=type=secret,id=extra_ca,target=/run/secrets/extra_ca \
    sh -c 'if [ -s /run/secrets/extra_ca ]; then export SSL_CERT_FILE=/run/secrets/extra_ca; fi; \
           uv pip install --python /app/.venv/bin/python pytest==9.1.1'

FROM runtime AS test
COPY --from=test-builder /app/.venv /app/.venv
COPY --chown=satya:satya services/worker/tests /app/tests
COPY --chown=satya:satya pyproject.toml /app/pyproject.toml
CMD ["pytest", "-m", "integration", "-p", "no:cacheprovider", "/app/tests"]
