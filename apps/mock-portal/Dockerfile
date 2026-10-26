# syntax=docker/dockerfile:1.7
# Approval Portal (Mock, for demo), Next.js standalone. Build context: repository root (pnpm workspace).
# Optional build secret `extra_ca`: CA bundle for build-time downloads behind a TLS proxy.
ARG NODE_IMAGE=node:24.22.1-alpine

FROM ${NODE_IMAGE} AS build
ENV CI=true NEXT_TELEMETRY_DISABLED=1 PNPM_HOME=/pnpm PATH=/pnpm:$PATH
WORKDIR /repo
RUN --mount=type=secret,id=extra_ca,target=/run/secrets/extra_ca \
    sh -c 'if [ -s /run/secrets/extra_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/extra_ca; fi; \
           npm install -g --no-fund --no-audit pnpm@10.28.0'
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml .npmrc ./
COPY apps/web/package.json apps/web/
COPY apps/mock-portal/package.json apps/mock-portal/
COPY packages/shared-types/package.json packages/shared-types/
RUN --mount=type=secret,id=extra_ca,target=/run/secrets/extra_ca \
    --mount=type=cache,id=pnpm-store,target=/pnpm/store \
    sh -c 'if [ -s /run/secrets/extra_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/extra_ca; fi; \
           pnpm install --frozen-lockfile --filter @satya/mock-portal... --store-dir /pnpm/store'
COPY packages/shared-types packages/shared-types
COPY apps/mock-portal apps/mock-portal
RUN pnpm --filter @satya/mock-portal exec next build

FROM ${NODE_IMAGE} AS runtime
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
WORKDIR /app
COPY --from=build --chown=node:node /repo/apps/mock-portal/.next/standalone ./
COPY --from=build --chown=node:node /repo/apps/mock-portal/.next/static ./apps/mock-portal/.next/static
USER node
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3000/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
CMD ["node", "apps/mock-portal/server.js"]
