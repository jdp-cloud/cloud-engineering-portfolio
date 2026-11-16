# What failed and how I fixed it

## 1. Web tasks failed container health checks on Fargate

Screenshots: `evidence/09-web-deployment-failed-console.png` and `evidence/10-web-health-check-root-cause.png`.

### Symptom

The `p07-staging-web` deployment was marked FAILED by the ECS deployment circuit breaker. ECS replaced the web tasks about every 4 minutes. The Application Load Balancer target group for the web service stayed healthy.

### How it was diagnosed

The ECS service events showed the circuit breaker stopping the deployment after repeated task failures. Each stopped task had an unhealthy container health status. The web log line was `Network: http://ip-10-70-0-37.ec2.internal:3000`.

### Root cause

The web image set `HOSTNAME=0.0.0.0` with an image `ENV` instruction. Fargate overrides an image `ENV HOSTNAME` with the task hostname. The Next.js standalone server reads `HOSTNAME` and binds only that address. The container health check requests `http://127.0.0.1:3000/healthz`, and nothing was listening there, so the check failed and ECS replaced the task. The load balancer target check connects to the task IP, which is the address the server did bind, so the target stayed healthy. The API was unaffected: `server.ts` calls `listen` on `0.0.0.0` and does not use `HOSTNAME`.

### Fix

`apps/web/Dockerfile` no longer sets `HOSTNAME` as an image environment variable. The runtime command is `["/usr/bin/env", "HOSTNAME=0.0.0.0", "node", "server.js"]`. That assignment is applied to the `node` process after the runtime has injected the task hostname, so the server binds `0.0.0.0`. The command is exec form, with no shell. `env` replaces itself with `node`, so `node` still receives `SIGTERM` directly.

### CI regression guard

The `image-scan` job in `.github/workflows/p07-ci.yml` starts the image it just built, after the build and before Trivy. It passes `-e HOSTNAME=ip-10-70-0-37.ec2.internal` and `APP_VERSION=ci`. The API run also passes `GREETING=ci`. The job waits up to 60 seconds for Docker's health status to become `healthy`. If it does not, the job prints `docker logs` and fails. The same step runs for web and for api.

The local and CI reproduction is a stand-in, not an exact copy of Fargate. The fake hostname does not resolve off AWS, so the old image exits with `getaddrinfo ENOTFOUND`. On Fargate the hostname resolves and Next.js binds only the task IP. Both cases fail the guard, and the fixed image passes both.

### Lesson

An ALB target health check and a container health check test different network paths. The target check reached the task IP. The container check reached `127.0.0.1`. Passing one does not prove the other.

Verified on Fargate: pending the first pipeline deploy.

## 2. CI image scan blocked on base-OS apt CVE

### Symptom

Trivy reported HIGH CVE-2026-109518 on the Debian 12.15 packages `apt` and `libapt-pkg6.0`. Both were installed at 2.6.1. The fixed version is 2.6.2. The image-scan jobs for api and web failed. The app code and `node_modules` were clean.

### Root cause

The pinned `node:24.22.2-bookworm-slim` digest was built before the Debian security update that shipped apt 2.6.2.

### Fix

The runtime stage in `apps/api/Dockerfile` and `apps/web/Dockerfile` upgrades `apt` and `libapt-pkg6.0` as root, before `USER node`. The pinned node digest is unchanged. `dpkg-query` on the local images reported 2.6.2 for both packages.

### Lesson

Pinned digests need periodic bumps. The scan gate caught this before deploy.

## 3. Single-service rollback smoke test required matching versions

### Symptom

The rollback workflow always passed `any` to the smoke test. That mode requires `/healthz` and `/api/health` to report the same version. Rolling back only api or only web leaves the other service on its current version, so the check fails when both endpoints are healthy.

### Root cause

`any` is the right check when both services move together. It is the wrong check when one service is rolled back and the other stays put.

### Fix

The smoke test accepts `independent`. Both endpoints must still return HTTP 200 and a non-empty version, and the versions are not compared. `p07-rollback.yml` passes `any` only when `service` is `both`, and `independent` otherwise.

### Lesson

A version-equality check is only valid when the rollback moved both services to the same version.
