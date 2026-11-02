# node:24.22.2-bookworm-slim
# Pinned by the manifest-list digest so amd64 and arm64 resolve the same image.
FROM node@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM deps AS build
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# node:24.22.2-bookworm-slim
FROM node@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000
# Standalone output already contains the traced production dependencies.
# Files stay root-owned. The node user can read them and cannot change them.
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
# Next writes image and fetch cache here at runtime. This directory is the only one node owns.
RUN mkdir -p /app/.next/cache && chown node:node /app/.next/cache
# Runtime never uses npm. Removing it drops the 6 HIGH findings in npm's own dependencies.
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack
USER node
EXPOSE 3000
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=10 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3000/healthz').then((r)=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
# HOSTNAME is set here, not with an image ENV. On Fargate the runtime overrides
# an image ENV HOSTNAME with the task hostname. The Next.js standalone server
# then listens only on that address, and the container health check against
# 127.0.0.1:3000 fails. /usr/bin/env applies this value for node and execs it,
# so node still receives SIGTERM directly.
CMD ["/usr/bin/env", "HOSTNAME=0.0.0.0", "node", "server.js"]
