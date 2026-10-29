# syntax=docker/dockerfile:1.7
# SATYA gateway image. Build context: repository root (uv workspace).
# Optional build secret `extra_ca`: a CA bundle for build-time downloads behind a TLS proxy.
# It is mounted only during RUN steps and never stored in an image layer.
ARG PYTHON_IMAGE=python:3.13.17-slim-trixie
# WITH_OCR=1 installs the real OCR engine (PaddleOCR) and bakes its models into the image at build
# time; the running container never downloads anything. Default off here, on in docker-compose.
ARG WITH_OCR=0

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
COPY packages/ocr/pyproject.toml packages/ocr/
RUN --mount=type=secret,id=extra_ca,target=/run/secrets/extra_ca \
    --mount=type=cache,target=/root/.cache/uv \
    sh -c 'if [ -s /run/secrets/extra_ca ]; then export SSL_CERT_FILE=/run/secrets/extra_ca; fi; \
           uv sync --frozen --no-dev --no-install-workspace --package satya-api'
COPY packages/shared-types/python packages/shared-types/python
COPY packages/affidavit packages/affidavit
COPY packages/forensics packages/forensics
COPY packages/ocr packages/ocr
COPY services/api services/api
RUN --mount=type=secret,id=extra_ca,target=/run/secrets/extra_ca \
    --mount=type=cache,target=/root/.cache/uv \
    sh -c 'if [ -s /run/secrets/extra_ca ]; then export SSL_CERT_FILE=/run/secrets/extra_ca; fi; \
           uv sync --frozen --no-dev --no-editable --package satya-api'
ARG WITH_OCR
RUN if [ "$WITH_OCR" = "1" ]; then apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 && rm -rf /var/lib/apt/lists/*; fi
RUN --mount=type=secret,id=extra_ca,target=/run/secrets/extra_ca \
    --mount=type=cache,target=/root/.cache/uv \
    sh -c 'if [ "$WITH_OCR" = "1" ]; then \
             if [ -s /run/secrets/extra_ca ]; then export SSL_CERT_FILE=/run/secrets/extra_ca REQUESTS_CA_BUNDLE=/run/secrets/extra_ca; fi; \
             uv pip install --python /app/.venv/bin/python -r packages/ocr/requirements-ocr.txt && \
             /app/.venv/bin/python packages/ocr/scripts/fetch_models.py /opt/ocr-models; \
           else mkdir -p /opt/ocr-models; fi'

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/app/.venv/bin:$PATH
RUN groupadd --system --gid 10001 satya && useradd --system --uid 10001 --gid satya --no-create-home satya
WORKDIR /app
ARG WITH_OCR
# PaddleOCR needs these shared libraries (OpenCV, OpenMP); nothing else is added.
RUN if [ "$WITH_OCR" = "1" ]; then \
      apt-get update && apt-get install -y --no-install-recommends libgomp1 libglib2.0-0 libgl1 \
      && rm -rf /var/lib/apt/lists/*; fi
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /opt/ocr-models /opt/ocr-models
COPY services/api/alembic.ini services/api/alembic.ini
COPY services/api/migrations services/api/migrations
# M5 (P-3) / M6 (P-4, P-18): year-versioned template profiles, versioned rules, the synthetic demo
# cases, the public half of the synthetic test PKI (TEST TRUST ANCHOR) and the synthetic register
# of earlier filings (all read-only).
COPY packages/templates /app/packages/templates
COPY packages/rules /app/packages/rules
COPY data/synthetic/cases /app/data/synthetic/cases
COPY data/synthetic/pki /app/data/synthetic/pki
COPY data/synthetic/registry /app/data/synthetic/registry
ENV SATYA_TEMPLATES_DIR=/app/packages/templates SATYA_RULES_DIR=/app/packages/rules \
    SATYA_DEMO_CASES_DIR=/app/data/synthetic/cases \
    SATYA_OCR_MODEL_DIR=/opt/ocr-models PADDLE_PDX_CACHE_HOME=/tmp/paddlex \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True HF_HUB_OFFLINE=1
RUN mkdir -p /var/lib/satya/uploads && chown satya:satya /var/lib/satya/uploads
USER satya
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/v1/health/live', timeout=3).status == 200 else 1)"]
CMD ["uvicorn", "satya_api.main:app", "--factory", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*", "--no-server-header", "--no-access-log"]
