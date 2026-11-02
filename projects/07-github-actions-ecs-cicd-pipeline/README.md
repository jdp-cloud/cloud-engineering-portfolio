# GitHub Actions to ECS CI/CD pipeline

Phase 1 is two small services and a local nginx stand-in for the load balancer path split. Phase 2 is Terraform under `terraform/`. Phase 3 is the workflows `.github/workflows/p07-ci.yml`, `p07-build-and-deploy.yml`, and `p07-rollback.yml`. The portfolio write-up comes later.

A small SaaS company runs a Next.js web app and a Node.js API. They deploy by hand from a laptop. This project is a working reference for a pipeline the whole team can run. The clicks for environments, variables, and the required check are in `docs/github-setup.md`.

## TODO before the first merge

Upgrade `next` and `eslint-config-next` from 16.4.4 to the Next.js security release scheduled for November 3, 2026 before any image from this project is pushed or deployed. That release covers seven medium vulnerabilities. Checked 2026-11-02: `npm view next dist-tags.latest` is still 16.4.4, so the pin stays. Do not merge to main until that release is in.

The deploy workflow runs `scripts/smoke-test.sh` against the load balancer. It calls `/healthz` and `/api/health`, and both `version` fields must match `v1.0.<run number>`. Rollback passes `any`, which only checks that the two versions match each other. The ALB sends `/api/*` to the API and every other path to web, so `/health` on the public URL lands on web. The API route `GET /health` is only for the target group health check, which hits the task directly. `/api/health` returns the same body on a path the ALB sends to the API.

## What is here

| Piece | Role |
| --- | --- |
| `apps/api` | Express API. `GET /health` and `GET /api/health` return `{ "status": "ok", "version": "<APP_VERSION>" }`. `GET /api/hello` returns `{ "message": "<GREETING>" }`. Missing values fall back to `dev` and `hello`. |
| `apps/web` | Next.js app, `output: "standalone"`. The page shows `APP_VERSION` and the browser calls `/api/hello`. `GET /healthz` returns `{ "status": "ok", "version": "<APP_VERSION>" }`. |
| `apps/docker-compose.yml` | Local only. nginx sends `/api/` to the API and everything else to web, on `127.0.0.1:8080`. |
| `terraform/` | Bootstrap (roles, ECR, budget) and the staging and production stacks. Bootstrap is applied. Apply both environments before the first merge. The GitHub OIDC provider is looked up, not created. |
| `docs/first-deploy-order.md` | Order of operations: bootstrap, first image push, staging, production, GitHub setup, then teardown. |
| `docs/github-setup.md` | Environments, variables, and the `p07-ci-result` ruleset. |

`APP_VERSION` and `GREETING` are read when a request arrives. They are not written into the image at build time.

Both images use Node.js 24.22.2 (`node:24.22.2-bookworm-slim`), pinned by digest. `engines` in both `package.json` files is `>=24.22.2 <25`. Both apps use TypeScript 6.0.3. The web app is on Next.js 16.4.4 until the upgrade in the TODO above.

## Known dev-only advisories

The web app pins ESLint at 9.39.5 because `eslint-config-next` 16.4.4 depends on `eslint-plugin-react`, `eslint-plugin-import`, and `eslint-plugin-jsx-a11y`, and those plugins' peer ranges stop at ESLint `^9`. The API uses ESLint 10.14.0 with `@eslint/js` 10.0.1 (there is no `@eslint/js` 10.14.0). Full `npm audit` still reports a moderate `minimatch` advisory (GHSA-g3hv-75wg-m249, versions below 11.0.1) through those devDependencies in both apps. `npm audit --omit=dev` reports 0 vulnerabilities in each. No devDependencies ship in the runtime images. The API image copies `node_modules` from a production-only `npm ci --omit=dev` stage, and the web image keeps only the files Next traces for the standalone server. Both runtime stages delete npm, npx, and corepack.

## Run it locally

Prerequisites: Node.js 24.22.2, npm, and Docker with Compose v2.

Lint and tests:

```bash
cd projects/07-github-actions-ecs-cicd-pipeline/apps/api
npm ci
npm run lint
npm test

cd ../web
npm ci
npm run lint
npm test
```

Each image on its own. The version and greeting are set on the running container, not at build time.

```bash
cd projects/07-github-actions-ecs-cicd-pipeline/apps

docker build -t p07-api:local ./api
docker build -t p07-web:local ./web

docker run -d --name p07-api-direct -p 127.0.0.1:3001:3001 \
  -e APP_VERSION=runtime-proof -e GREETING=from-the-env p07-api:local
docker run -d --name p07-web-direct -p 127.0.0.1:3000:3000 \
  -e APP_VERSION=runtime-proof p07-web:local

curl -sS http://127.0.0.1:3001/health
curl -sS http://127.0.0.1:3001/api/health
curl -sS http://127.0.0.1:3001/api/hello
curl -sS http://127.0.0.1:3000/healthz
curl -sS http://127.0.0.1:3000/

docker rm -f p07-api-direct p07-web-direct
```

Expected API bodies: `{"status":"ok","version":"runtime-proof"}` on both health routes, and `{"message":"from-the-env"}` on `/api/hello`. `/healthz` returns the same status and version. The HTML from `/` includes `runtime-proof`.

Path split through nginx:

```bash
cd projects/07-github-actions-ecs-cicd-pipeline/apps
docker compose up -d --build --wait

curl -sS http://127.0.0.1:8080/healthz
curl -sS http://127.0.0.1:8080/api/health
curl -sS http://127.0.0.1:8080/api/hello
curl -sS http://127.0.0.1:8080/

docker compose down
```

With the compose file's environment, `/healthz` and `/api/health` report version `local`, and `/api/hello` returns `{"message":"hello"}`. `/` is the web page, and the HTML includes that version. `GET /health` on port 8080 is not the API: the path is outside `/api/`, so nginx sends it to web, which responds 404.
