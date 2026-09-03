# Argo CD GitOps and RBAC on Kubernetes

This project reproduces and extends an instructor-led Argo CD lab on a local Kubernetes cluster. The work focuses on GitOps deployment, drift reconciliation, Argo CD `AppProject` boundaries, and least-privilege RBAC.

The lab was rebuilt on a clean Minikube profile and validated against my own public GitHub portfolio repository. During the rebuild, I diagnosed an incomplete training installation, replaced the partial Argo CD control-plane resources with the official pinned Argo CD v2.10.7 install manifest, and then completed the GitOps and authorization tests.

> **Scope:** This is a local portfolio lab, not a production deployment. Names such as `splunk-prod` represent logical environment boundaries inside the lab.

## What this project demonstrates

- Deploying and validating Argo CD on Kubernetes
- Diagnosing missing Argo CD service accounts, RBAC resources, and CRDs
- Replacing an incomplete install with the official version-matched upstream manifest
- Deploying an application from Git with Argo CD
- Validating automated reconciliation and self-healing after live drift
- Restricting application destinations with Argo CD `AppProject`
- Testing an intentionally invalid cross-environment destination
- Configuring a restricted local Argo CD identity
- Allowing non-production sync while denying production-designated sync
- Verifying that an administrator can perform the same production-designated sync successfully
- Troubleshooting an Argo CD CLI/server version mismatch

## Architecture

```text
Local Git workspace
        |
        v
GitHub: jdp-cloud/cloud-engineering-portfolio
        |
        v
Argo CD v2.10.7
        |
        v
Minikube profile: argocd
        |
        +--> splunk workload from Lab 01
        |
        +--> AppProject environment boundaries
        |
        +--> RBAC validation workload
```

## Environment

| Component | Configuration |
| --- | --- |
| Host | Apple Silicon Mac mini |
| Kubernetes | Minikube, dedicated `argocd` profile |
| Minikube driver | `vfkit` with Rosetta support |
| Kubernetes version | v1.35.1 |
| Argo CD server | v2.10.7 |
| Argo CD CLI used for final validation | v2.10.7 |
| Git source | `https://github.com/jdp-cloud/cloud-engineering-portfolio.git` |

## Repository layout

```text
02-argocd-gitops/
├── README.md
├── manifests/
│   ├── 01-argocd-namespace.yaml
│   ├── 02-splunk-application.yaml
│   ├── 03-argocd-local-account.yaml
│   ├── 04-argocd-rbac.yaml
│   ├── appprojects/
│   │   ├── 01-splunk-dev-project.yaml
│   │   ├── 02-splunk-test-project.yaml
│   │   └── 03-splunk-prod-project.yaml
│   └── rbac-tests/
│       ├── 01-rbac-demo-dev.yaml
│       └── 02-rbac-demo-prod.yaml
├── workloads/
│   └── rbac-demo/
│       └── configmap.yaml
├── tests/
│   └── 01-prod-wrong-destination.yaml
├── evidence/
│   ├── command-output/
│   └── screenshots/
└── notes/
    └── troubleshooting.md
```

Instructor-supplied reference material and the full upstream Argo CD install manifest were kept separate during the lab and are not part of the public project files.

## 1. Clean cluster baseline

I created a dedicated Minikube profile named `argocd` so the GitOps work did not modify the earlier Splunk lab cluster.

The initial cluster had only the default Kubernetes namespaces and no Argo CD `Application` or `AppProject` CRDs.

Evidence:

- `evidence/command-output/01-argocd-clean-cluster-baseline.txt`
- `evidence/screenshots/01-argocd-clean-cluster-baseline.png`

## 2. Diagnose the partial Argo CD installation

I first followed the instructor workflow and applied the supplied Argo CD component manifests.

The repository server and application controller started, but `argocd-server` could not become healthy. Previous-container logs showed authorization errors for the default service account, including failures to list ConfigMaps and Secrets.

Additional checks showed:

- the Argo CD components were using the Kubernetes `default` service account
- expected Argo CD Roles and RoleBindings were missing
- Argo CD ClusterRoles and ClusterRoleBindings were missing
- `Application`, `ApplicationSet`, and `AppProject` CRDs were missing

I did not solve this by granting broad permissions to the default service account.

Instead, I removed the partial runtime resources while preserving the `argocd` namespace.

Evidence:

- `evidence/command-output/05-argocd-server-previous.log`
- `evidence/command-output/06-argocd-server-describe.txt`
- `evidence/command-output/07-argocd-rbac-crd-diagnosis.txt`
- `evidence/screenshots/02-argocd-missing-rbac-crds.png`

## 3. Install the complete pinned Argo CD release

I downloaded the official Argo CD v2.10.7 install manifest and inspected its resource inventory before applying it.

The upstream manifest included the missing control-plane resources, including:

- 7 ServiceAccounts
- 5 Roles
- 5 RoleBindings
- 3 ClusterRoles
- 3 ClusterRoleBindings
- 3 CRDs

After installation, all Argo CD components were healthy and the expected CRDs were available.

Upstream source:

- [Argo CD v2.10.7 install manifest](https://raw.githubusercontent.com/argoproj/argo-cd/v2.10.7/manifests/install.yaml)

Evidence:

- `evidence/command-output/08-argocd-upstream-resource-inventory.txt`
- `evidence/command-output/10-argocd-upstream-install.txt`
- `evidence/command-output/11-argocd-full-install-validation.txt`
- `evidence/screenshots/03-argocd-full-install-healthy.png`
- `evidence/screenshots/04-argocd-ui-login-success.png`

## 4. Deploy the Splunk workload through GitOps

I created an Argo CD `Application` that points to the published Kubernetes manifests from Lab 01:

```text
projects/01-kubernetes-stateful-application/manifests
```

The Argo CD Application source uses:

```text
https://github.com/jdp-cloud/cloud-engineering-portfolio.git
```

The workload retained its runtime-only `splunk-secret`; no secret value was committed to Git.

Because the Splunk container image is amd64-only in this lab environment, I preloaded the image into the Apple Silicon Minikube VM using Rosetta support before synchronization.

Argo CD synchronized the workload successfully and reported:

```text
Sync:   Synced
Health: Healthy
```

The synchronized revision matched the published Lab 01 commit.

Evidence:

- `evidence/command-output/12-splunk-argocd-application-created.txt`
- `evidence/command-output/13-splunk-gitops-sync-validation.txt`
- `evidence/screenshots/05-argocd-splunk-synced-healthy.png`

## 5. Validate self-healing

The Application was configured with automated synchronization and self-healing.

To test reconciliation, I changed the live `splunk-config` ConfigMap directly from `--accept-license` to `--accept-license --drift-test`.

Argo CD detected the drift and restored the Git-defined value `--accept-license`. The Application returned to `Synced` and `Healthy`.

Evidence:

- `evidence/command-output/14-argocd-self-heal-validation.txt`
- `evidence/screenshots/06-argocd-self-heal-validation.png`

## 6. Enforce environment boundaries with AppProject

I created three Argo CD `AppProject` resources:

- `splunk-dev`
- `splunk-test`
- `splunk-prod`

Each project permits the portfolio repository as a source but restricts deployment to its matching namespace.

For example, `splunk-prod` permits only:

```text
namespace: splunk-prod
server: https://kubernetes.default.svc
```

### Negative destination test

I created an intentionally invalid Argo CD Application that declared:

```text
project: splunk-prod
destination namespace: splunk-dev
```

Kubernetes accepted the `Application` custom resource, but Argo CD rejected its specification with `InvalidSpecError` because the requested destination did not match the `splunk-prod` project policy.

Evidence:

- `tests/01-prod-wrong-destination.yaml`
- `evidence/screenshots/07-appproject-destination-policy-denied.png`

## 7. Configure least-privilege Argo CD RBAC

For the local lab, I created a restricted Argo CD account named `platform-operator` and mapped it to `role:nonprod-operator`.

The role allows application sync in the dev and test projects and explicitly denies sync in the prod-designated project.

The local account is a lab identity. In a production environment, the same authorization pattern would normally be associated with an SSO or identity-provider group rather than a standalone local account.

Policy validation returned:

```text
DEV sync:   yes
TEST sync:  yes
PROD sync:  no
```

Evidence:

- `manifests/03-argocd-local-account.yaml`
- `manifests/04-argocd-rbac.yaml`
- `evidence/command-output/19-argocd-rbac-validation.txt`
- `evidence/screenshots/08-argocd-rbac-nonprod-allow-prod-deny.png`

## 8. Prove RBAC with real sync operations

To test authorization with real operations without running additional Splunk instances, I added a lightweight ConfigMap workload to the portfolio repository:

```text
projects/02-argocd-gitops/workloads/rbac-demo/configmap.yaml
```

Two manual-sync Applications used the same Git source:

- `rbac-demo-dev` in project `splunk-dev`
- `rbac-demo-prod` in project `splunk-prod`

### Restricted operator result

Authenticated as `platform-operator`:

- DEV sync succeeded
- DEV became `Synced / Healthy`
- the DEV ConfigMap was created
- PROD sync returned `PermissionDenied`
- PROD remained `OutOfSync`
- the PROD ConfigMap did not exist

The denial identified the restricted subject and protected application:

```text
permission denied: applications, sync, splunk-prod/rbac-demo-prod
```

Evidence:

- `evidence/command-output/21-argocd-rbac-enforcement-validation.txt`
- `evidence/screenshots/09-argocd-rbac-prod-sync-denied.png`

### Administrator result

I then authenticated as `admin` and synchronized the same prod-designated Application.

The sync succeeded, the Application became `Synced / Healthy`, and the ConfigMap was created in `splunk-prod`.

This confirmed that the earlier failure was an RBAC authorization decision rather than a broken Application, namespace, or Git source.

Evidence:

- `evidence/command-output/22-argocd-admin-prod-sync-validation.txt`
- `evidence/screenshots/10-argocd-admin-prod-sync-allowed.png`

The temporary RBAC test Applications and namespaces were deleted after validation.

## Validation summary

| Validation | Result |
| --- | --- |
| Clean Argo CD cluster baseline | Passed |
| Complete Argo CD control plane | Passed |
| Git repository synchronization | `Synced / Healthy` |
| Live drift reconciliation | Git-defined value restored |
| AppProject destination restriction | Invalid destination rejected |
| DEV sync authorization | Allowed |
| TEST sync authorization | Allowed |
| PROD sync authorization for restricted operator | Denied |
| Real DEV sync as restricted operator | Succeeded |
| Real PROD sync as restricted operator | `PermissionDenied` |
| PROD workload after denied sync | Not created |
| Real PROD sync as admin | Succeeded |

## Security decisions

- Runtime secret values were not committed to Git.
- Passwords were not stored in evidence files.
- The incomplete training install was not repaired by broadening the Kubernetes default service account.
- Environment destinations were restricted through `AppProject`.
- The restricted operator received only the synchronization permissions needed for non-production projects.
- Production-designated sync was explicitly denied for the restricted identity.
- Temporary authorization-test resources were removed after validation.
- Instructor and upstream reference files were kept separate from authored project files.

## Troubleshooting highlight: CLI/server version mismatch

The locally installed Homebrew Argo CD CLI was v3.5.1 while the lab server was intentionally pinned to v2.10.7.

CLI login attempts through `kubectl port-forward` caused connection resets even though HTTPS connectivity to the Argo CD UI returned HTTP 200.

Before disabling Tailscale or Bitdefender, I checked the CLI and server versions. I installed a separate Argo CD v2.10.7 Apple Silicon CLI and retried the same login. The version-matched CLI logged in successfully.

For the complete troubleshooting sequence, see [`notes/troubleshooting.md`](notes/troubleshooting.md).

## Project context and attribution

This project began from the current Argo CD materials in the instructor repository:

- [BalericaAI/kubernetesclass](https://github.com/BalericaAI/kubernetesclass)

I used the instructor workflow as the starting point, then reproduced the lab on a clean cluster, adapted repository and environment references to my own GitHub project, diagnosed the incomplete control-plane installation, replaced it with the official pinned Argo CD release, and added validation for self-healing, AppProject boundaries, and real RBAC enforcement.

Instructor-supplied files are not presented as authored portfolio work.

## Scope and limitations

This project intentionally does not claim:

- a production Argo CD deployment
- high availability
- a managed Kubernetes service
- external SSO or identity-provider integration
- production Splunk operations
- OPA or Gatekeeper policy enforcement

The `dev`, `test`, and `prod` names represent authorization and environment boundaries inside a local Kubernetes lab.
