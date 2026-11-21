# node:24.22.2-bookworm-slim
# Pinned by the manifest-list digest so amd64 and arm64 resolve the same image.
FROM node@sha256:e18c3ccdf7d71619990b0e85639f506e2028a95410999cab24cc373cbd10e0ac AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM deps AS build
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

# Production dependencies only. The runtime stage copies these as root-owned files.
# --ignore-scripts: this image does not need package install scripts.
FROM node@sha256:e18c3ccdf7d71619990b0e85639f506e2028a95410999cab24cc373cbd10e0ac AS prod-deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts

# node:24.22.2-bookworm-slim
FROM node@sha256:e18c3ccdf7d71619990b0e85639f506e2028a95410999cab24cc373cbd10e0ac AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    PORT=3001
COPY package.json package-lock.json ./
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
# Runtime never uses npm. Removing it drops the 6 HIGH findings in npm's own dependencies.
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack
# Patch base-OS apt (CVE-2026-109518) until the pinned node digest is bumped.
RUN apt-get update && apt-get install -y --no-install-recommends --only-upgrade apt libapt-pkg6.0 && rm -rf /var/lib/apt/lists/*
USER node
EXPOSE 3001
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=10 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3001/health').then((r)=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
CMD ["node", "dist/server.js"]
