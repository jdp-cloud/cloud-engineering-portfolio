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

## Project 04: Terraform (87 failed checks)

Scanned in CI on pull request 7 (2026-10-01). That run reported 184 failed Terraform checks in total: 97 in project 03 (the same count as the first scan) and 87 in project 04. Many findings repeat because the stack has 7 Lambda functions, 8 log groups and 5 DynamoDB tables.

### Worth fixing (14)

Cheap changes with a real security benefit.

| Finding | Checks | Count | Notes |
| --- | --- | --- | --- |
| Lambdas have no dead-letter queue | `CKV_AWS_116` | 7 | Matters most for the SOAR Lambda, which EventBridge calls asynchronously. A failed invocation is currently lost after retries. |
| SNS topics not encrypted | `CKV_AWS_26` | 2 | One argument per topic (`kms_master_key_id`). |
| WAF has no Log4j / known-bad-inputs rule | `CKV_AWS_192`, `CKV2_AWS_77` | 2 | Add the AWS managed `AWSManagedRulesKnownBadInputsRuleSet` next to the Common Rule Set. |
| API Gateway stage has no access logging | `CKV_AWS_76`, `CKV2_AWS_4` | 2 | The WAF logs blocked requests, but allowed requests leave no access record. |
| API method does not validate requests | `CKV2_AWS_53` | 1 | Add a request validator to the `analyze` method. |

### Lab trade-offs (73)

Left off deliberately to keep cost low and teardown clean. None of these is a claim about production readiness.

| Finding | Checks | Count | Why it is there |
| --- | --- | --- | --- |
| Lambda hardening: code signing, VPC, X-Ray, reserved concurrency, customer-managed key for environment variables | `CKV_AWS_272`, `CKV_AWS_117`, `CKV_AWS_50`, `CKV_AWS_115`, `CKV_AWS_173` | 35 | The Lambdas only call AWS service APIs, so a VPC would add NAT cost for no isolation gain. Signing, tracing and concurrency limits add setup for a short-lived lab. |
| CloudWatch log groups: no customer-managed key, retention under one year | `CKV_AWS_158`, `CKV_AWS_338` | 16 | Retention defaults to 7 days (`log_retention_days`) so logs do not accumulate cost. |
| DynamoDB: no customer-managed key, point-in-time recovery off | `CKV_AWS_119`, `CKV_AWS_28` | 10 | Recovery is a variable (`enable_point_in_time_recovery`, default false). Tables use the AWS-owned key, and a customer-managed key adds a monthly cost and a deletion delay that gets in the way of teardown. |
| Report bucket: AES256 not KMS, no access logging, replication, lifecycle or event notifications | `CKV_AWS_145`, `CKV_AWS_18`, `CKV_AWS_144`, `CKV2_AWS_61`, `CKV2_AWS_62` | 5 | The bucket is encrypted and blocks public access. The rest are production features. `force_destroy` is a variable so the lab can be removed. |
| EventBridge Scheduler: no customer-managed key | `CKV_AWS_297` | 3 | Same cost and teardown reasoning as DynamoDB. |
| API Gateway: no caching, no client certificate, no X-Ray, no create-before-destroy | `CKV_AWS_120`, `CKV2_AWS_51`, `CKV_AWS_73`, `CKV_AWS_237` | 4 | Low traffic, and the API authenticates callers with Cognito instead of client certificates. |

## Project 05: Terraform (0 failed checks, 3 skipped)

Scanned locally with Checkov 3.3.22 (Terraform framework) before the pull request: **134 passed, 0 failed, 3 skipped.** Every skip is an inline `checkov:skip` comment with its reason next to the resource, so none of them is hidden in the workflow configuration.

| Skipped check | Resource | Reason recorded in the code |
| --- | --- | --- |
| `CKV_GCP_38` | Test VM | A disposable lab VM that holds no data. Google-managed encryption at rest is enough. Customer-supplied or customer-managed keys are a production step. |
| `CKV_AWS_394` | Availability Zone data source | Only the first zone name is used, so a newly added zone cannot change the result. |
| `CKV2_AWS_5` | Endpoint security group | It is attached to the SSM interface endpoints through `for_each`, which the check cannot follow. |

This is a smaller stack than projects 03 and 04 (47 resource blocks, no web tier or Lambda functions), and it was written with the scanner in mind: flow logs are on, the log group uses a customer-managed key, the test instance requires IMDSv2, and nothing is open to `0.0.0.0/0`. The result says the Terraform follows the checks Checkov knows. It does not say the VPN works, because the project has not been deployed from this copy.

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
