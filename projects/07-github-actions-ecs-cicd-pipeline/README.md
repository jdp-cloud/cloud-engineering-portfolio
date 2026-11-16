# GitHub Actions to ECS CI/CD pipeline

A small SaaS team runs a Next.js web app and a Node.js API and deploys both by hand from a laptop. The workflows build each image once, deploy that digest to ECS in staging, and deploy the same digest to production only after a required reviewer approves, assuming IAM roles with GitHub OIDC instead of stored AWS keys. A rollback workflow can move one service or both back to an earlier task definition. Bootstrap is applied, staging was applied and later destroyed after a failed web deployment, production was never applied, and the deploy workflow stays off unless `P07_DEPLOY_ENABLED` is `true`.

## Deployment status

Bootstrap is applied. The apply added 11 resources, including the ECR repositories, the three GitHub Actions roles, and the monthly budget ([evidence/02-bootstrap-apply.png](evidence/02-bootstrap-apply.png)). In that output the `Project` cost allocation tag was Inactive. It was set to Active on 2026-11-02 ([evidence/03-cost-allocation-tag-active.png](evidence/03-cost-allocation-tag-active.png)).

I applied the staging stack with Terraform, not with GitHub Actions. Both services became stable, both target groups were healthy, and the load balancer returned version `dev` ([evidence/04-staging-first-deploy.png](evidence/04-staging-first-deploy.png)).

A later deployment of `p07-staging-web` failed. The ECS console shows that web deployment as Failed and the API deployment as Completed ([evidence/09-web-deployment-failed-console.png](evidence/09-web-deployment-failed-console.png)). The service events show tasks stopped for failed container health checks. The web log shows Next.js bound to the task hostname `ip-10-70-0-37.ec2.internal`, not to `0.0.0.0` ([evidence/10-web-health-check-root-cause.png](evidence/10-web-health-check-root-cause.png)). Fargate replaces an image `ENV HOSTNAME` with the task hostname, and the container health check calls `127.0.0.1`. The Dockerfile fix and the CI guard are in [docs/what-failed-and-how-i-fixed-it.md](docs/what-failed-and-how-i-fixed-it.md). That doc says the fix is still pending a check on Fargate. No screenshot shows a successful staging deploy after the fix.

I then destroyed staging. Terraform removed 32 resources, and the next lookup did not find a load balancer named `p07-staging` ([evidence/11-staging-destroy-verified.png](evidence/11-staging-destroy-verified.png)).

The production stack was not applied. The GitHub `production` environment has required reviewer `jdp-cloud`, Prevent self-review off, and deploys limited to `main` ([evidence/07-production-environment-approval-gate.png](evidence/07-production-environment-approval-gate.png)). The staging environment has no required reviewer and is also limited to `main` ([evidence/05-staging-environment.png](evidence/05-staging-environment.png)). The clicks for environments, variables, and the required check are in [docs/github-setup.md](docs/github-setup.md).

The build job runs only when the repository variable `P07_DEPLOY_ENABLED` is `true` ([p07-build-and-deploy.yml](../../.github/workflows/p07-build-and-deploy.yml)). The variables screenshot lists `AWS_REGION` and `P07_ECR_PUSH_ROLE_ARN` and does not show `P07_DEPLOY_ENABLED` ([evidence/08-actions-variables.png](evidence/08-actions-variables.png)). With that variable unset, the build job is skipped, and the staging and production jobs are skipped with it.

## What I proved

- **Same digest from staging to production is the workflow design.** [p07-build-and-deploy.yml](../../.github/workflows/p07-build-and-deploy.yml) builds the linux/amd64 images once and passes those digests to staging, then to production, without rebuilding. Production was never applied, so that promotion has not run.
- **The workflows assume roles with OIDC.** The build, deploy, and rollback jobs set `id-token: write` and `role-to-assume`. They do not store AWS access keys. Bootstrap recorded the existing GitHub OIDC provider ([evidence/02-bootstrap-apply.png](evidence/02-bootstrap-apply.png), [docs/github-setup.md](docs/github-setup.md)).
- **Production has a required reviewer.** [evidence/07-production-environment-approval-gate.png](evidence/07-production-environment-approval-gate.png). The production deploy job uses the `production` environment, so that rule applies. Prevent self-review is off.
- **The cost allocation tag is active.** `Project` is Status Active ([evidence/03-cost-allocation-tag-active.png](evidence/03-cost-allocation-tag-active.png)). Spend from before that activation is not backfilled ([docs/first-deploy-order.md](docs/first-deploy-order.md)).
- **The failed staging web deployment has a recorded cause.** The web service failed container health checks while the API deployment completed ([evidence/09-web-deployment-failed-console.png](evidence/09-web-deployment-failed-console.png), [evidence/10-web-health-check-root-cause.png](evidence/10-web-health-check-root-cause.png)). The image `ENV HOSTNAME` was replaced by the Fargate task hostname. The fix is in the web image command, and it has not been shown succeeding on Fargate ([docs/what-failed-and-how-i-fixed-it.md](docs/what-failed-and-how-i-fixed-it.md)).
- **Staging teardown removed the stack.** Terraform destroyed 32 resources, and the load balancer was not found afterwards ([evidence/11-staging-destroy-verified.png](evidence/11-staging-destroy-verified.png)). Bootstrap was not destroyed.
- **Pull request 59's image scan blocked a fixable base-image CVE.** Trivy reported HIGH CVE-2026-109518 in Debian 12.15 packages `apt` and `libapt-pkg6.0` (installed 2.6.1, fixed in 2.6.2). The app code and `node_modules` were clean. The runtime stage upgrades those two packages, and local `dpkg-query` reported 2.6.2 ([docs/what-failed-and-how-i-fixed-it.md](docs/what-failed-and-how-i-fixed-it.md)).

## Limitations

- Production was never applied. The approval gate is configured. No production deploy has run.
- Bootstrap is still applied: the IAM roles, the ECR repositories, and the budget. Staging is destroyed.
- The web and API apps are minimal demo services. They serve health and hello routes. They have no database and no authentication.
- The web health-check fix has not been verified on Fargate. [docs/what-failed-and-how-i-fixed-it.md](docs/what-failed-and-how-i-fixed-it.md) says that check is pending the first pipeline deploy. No screenshot shows a healthy staging deploy after the fix.
- The healthy staging run in [evidence/04-staging-first-deploy.png](evidence/04-staging-first-deploy.png) is a Terraform apply. There is no screenshot of a successful GitHub Actions deploy.
- The first image push uses the operator's own AWS credentials. Later pushes are meant to use the OIDC role ([docs/first-deploy-order.md](docs/first-deploy-order.md)).
- Prevent self-review is off, so the account that starts a production run can approve it ([docs/github-setup.md](docs/github-setup.md)).
- The CI image scan ignores unfixed findings. On 2026-11-02, `--ignore-unfixed` reported 0, and the same images had 33 ungated HIGH or CRITICAL Debian findings without that flag ([docs/image-scanning.md](docs/image-scanning.md)).
- The GitHub OIDC provider and the Terraform state bucket already existed. This project looks them up. It does not create them, and teardown does not delete the provider ([docs/first-deploy-order.md](docs/first-deploy-order.md)).

The web app is on Next.js 16.4.5. The November 2026 advisories are in [docs/dependency-security.md](docs/dependency-security.md).

The smoke test is [scripts/smoke-test.sh](scripts/smoke-test.sh). The deploy workflow runs it against the load balancer. It calls `/healthz` and `/api/health`, and both `version` fields must match `v1.0.<run number>`. Rollback of both services passes `any`, which only checks that the two versions match each other. Rollback of one service passes `independent`, which requires HTTP 200 and a non-empty version from both endpoints and does not compare the versions. The ALB sends `/api/*` to the API and every other path to web, so `/health` on the public URL lands on web. The API route `GET /health` is only for the target group health check, which hits the task directly. `/api/health` returns the same body on a path the ALB sends to the API.

## What is here

| Piece | Role |
| --- | --- |
| `apps/api` | Express API. `GET /health` and `GET /api/health` return `{ "status": "ok", "version": "<APP_VERSION>" }`. `GET /api/hello` returns `{ "message": "<GREETING>" }`. Missing values fall back to `dev` and `hello`. |
| `apps/web` | Next.js app, `output: "standalone"`. The page shows `APP_VERSION` and the browser calls `/api/hello`. `GET /healthz` returns `{ "status": "ok", "version": "<APP_VERSION>" }`. |
| `apps/docker-compose.yml` | Local only. nginx sends `/api/` to the API and everything else to web, on `127.0.0.1:8080`. |
| `terraform/` | Bootstrap (roles, ECR, budget) and the staging and production stacks. Bootstrap is applied. Staging was applied and later destroyed. Production was not applied. The GitHub OIDC provider is looked up, not created. |
| `docs/first-deploy-order.md` | Order of operations: bootstrap, first image push, staging, production, GitHub setup, then teardown. |
| `docs/github-setup.md` | Environments, variables, and the `p07-ci-result` ruleset. |

`APP_VERSION` and `GREETING` are read when a request arrives. They are not written into the image at build time.

Both images use Node.js 24.22.2 (`node:24.22.2-bookworm-slim`), pinned by digest. `engines` in both `package.json` files is `>=24.22.2 <25`. Both apps use TypeScript 6.0.3.

## Known dev-only advisories

The web app pins ESLint at 9.39.5 because `eslint-config-next` 16.4.5 depends on `eslint-plugin-react`, `eslint-plugin-import`, and `eslint-plugin-jsx-a11y`, and those plugins' peer ranges stop at ESLint `^9`. The API uses ESLint 10.14.0 with `@eslint/js` 10.0.1 (there is no `@eslint/js` 10.14.0). Full `npm audit` still reports a moderate `minimatch` advisory (GHSA-g3hv-75wg-m249, versions below 11.0.1) through those devDependencies in both apps. `npm audit --omit=dev` reports 0 vulnerabilities in each. No devDependencies ship in the runtime images. The API image copies `node_modules` from a production-only `npm ci --omit=dev` stage, and the web image keeps only the files Next traces for the standalone server. Both runtime stages delete npm, npx, and corepack.

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
