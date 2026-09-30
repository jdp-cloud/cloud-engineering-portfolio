# IaC scan findings

[Checkov](https://www.checkov.io/) scans the Terraform and Kubernetes manifests in `projects/` on every push and pull request (see [`.github/workflows/iac-security.yml`](../.github/workflows/iac-security.yml)). This page records what the first scan found and what I plan to do about it.

**First scan:** 2026-09-30, Checkov 3.3.21, run locally over `projects/` with the Terraform and Kubernetes frameworks.

| Framework | Passed | Failed |
| --- | --- | --- |
| Terraform (project 03) | 464 | 97 |
| Kubernetes (projects 01 and 02) | 77 | 18 |

The scan currently reports findings but does not fail the build. Checkov's free rule set has no severity levels, so it cannot gate on "high only". The plan is to fix the quick wins, record each intentional trade-off as a documented skip, then turn off `soft_fail` so any new finding blocks a merge.

## Project 03: Terraform (97 failed checks)

Many findings repeat because the same `web-stack` module is deployed in seven regions.

### Already disclosed as lab trade-offs (58)

These match the [Known limitations](../projects/03-multi-region-hub-and-spoke-web-application-with-centralized-siem/README.md#known-limitations) in the project README.

| Finding | Checks | Count | Why it is there |
| --- | --- | --- | --- |
| Load balancers use HTTP, not HTTPS, and accept port 80 from the internet | `CKV_AWS_260`, `CKV_AWS_2`, `CKV_AWS_378`, `CKV2_AWS_20`, `CKV_AWS_103` | 42 | The lab has no domain or certificate. A production version would terminate TLS on the ALB with an ACM certificate. |
| VPC Flow Logs not enabled | `CKV2_AWS_11` | 8 | Listed as not yet built. This is the one I most want to add. |
| Deletion protection off (Aurora and the ALBs) | `CKV_AWS_139`, `CKV_AWS_150` | 8 | Off so the lab can be destroyed cleanly after testing. The README states this for Aurora, and the ALBs follow the same reasoning. |

### Not yet addressed (39)

| Finding | Checks | Count | Notes |
| --- | --- | --- | --- |
| ALB access logging off | `CKV_AWS_91` | 7 | Would need an S3 bucket per region. Worth doing. |
| No WAF in front of the ALBs | `CKV2_AWS_28` | 7 | Adds ongoing cost. Reasonable to defer in a short-lived lab. |
| Auto Scaling group tags not propagated | `CKV_AWS_153` | 7 | Low risk. Easy fix. |
| Availability Zone data source not pinned | `CKV_AWS_394` | 8 | Low risk. Easy fix. |
| Aurora and EC2 hardening gaps | `CKV_AWS_327`, `CKV_AWS_325`, `CKV_AWS_324`, `CKV_AWS_326`, `CKV_AWS_353`, `CKV_AWS_118`, `CKV_AWS_226`, `CKV2_AWS_8`, `CKV_AWS_135`, `CKV_AWS_126` | 10 | Customer-managed KMS key, database audit logging, log export, backtracking, performance insights, enhanced monitoring, automatic minor upgrades, a backup plan, EBS-optimized and detailed monitoring. The audit logging and KMS key matter most for a security-focused design. |

## Projects 01 and 02: Kubernetes (18 failed checks)

Both are local Minikube labs, not production deployments. 17 findings are in the Splunk StatefulSet and pod (project 01). One is the demo ConfigMap in project 02, which uses the `default` namespace.

Project 01 already runs as a non-root user with a fixed UID and `fsGroup`, and creates the Splunk admin password at runtime. The scan shows what is still missing:

- CPU and memory requests and limits are not set.
- Liveness and readiness probes are not configured.
- The container image is not pinned by digest, and the pull policy is not `Always`.
- `allowPrivilegeEscalation` is not set to false, capabilities are not dropped, there is no seccomp profile and the root filesystem is writable.
- The secret is passed as an environment variable instead of a mounted file.
- The service account token is mounted by default, and no `NetworkPolicy` applies.

## Next steps

1. Fix the low-risk items: Auto Scaling group tags, Availability Zone pinning, and the Kubernetes security context and resource settings.
2. Add VPC Flow Logs and ALB access logging in project 03.
3. Add Aurora audit logging and a customer-managed KMS key.
4. Record a reasoned skip for each intentional trade-off (HTTP-only lab, deletion protection off, no WAF).
5. Turn off `soft_fail` so new findings block merges.
