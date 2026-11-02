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

### Lesson

An ALB target health check and a container health check test different network paths. The target check reached the task IP. The container check reached `127.0.0.1`. Passing one does not prove the other.
