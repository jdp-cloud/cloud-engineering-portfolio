# node:24.22.2-bookworm-slim
# Pinned by the manifest-list digest so amd64 and arm64 resolve the same image.
FROM node@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM deps AS build
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

# node:24.22.2-bookworm-slim
FROM node@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    PORT=3001
COPY package.json package-lock.json ./
# Production dependencies only, root-owned, so the node user can read them and cannot change them.
# --ignore-scripts: this image does not need package install scripts.
RUN npm ci --omit=dev --ignore-scripts && npm cache clean --force
COPY --from=build /app/dist ./dist
USER node
EXPOSE 3001
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=10 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3001/health').then((r)=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
CMD ["node", "dist/server.js"]
