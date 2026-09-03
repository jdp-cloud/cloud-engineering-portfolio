# Troubleshooting Notes

These notes capture the main failures encountered while rebuilding the Argo CD GitOps lab and the reasoning used to isolate them.

## 1. Argo CD server repeatedly failed after the training component install

### Symptom

After applying the instructor-provided Argo CD component manifests:

- the repository server became healthy
- the application controller became healthy
- `argocd-server` remained unready and restarted

Previous-container logs included authorization errors such as:

```text
User "system:serviceaccount:argocd:default" cannot list resource "configmaps"
User "system:serviceaccount:argocd:default" cannot list resource "secrets"
```

Pod inspection also showed failing health probes.

### Diagnostic process

I checked whether the service account could perform the operations reported in the logs:

```bash
kubectl auth can-i list configmaps \
  -n argocd \
  --as=system:serviceaccount:argocd:default

kubectl auth can-i list secrets \
  -n argocd \
  --as=system:serviceaccount:argocd:default
```

Both returned `no`.

I then inspected Argo CD Kubernetes authorization resources:

```bash
kubectl -n argocd get serviceaccounts,roles,rolebindings
kubectl get clusterroles,clusterrolebindings | grep argocd
```

The expected Argo CD RBAC resources were absent.

Finally, I checked for Argo CD CRDs:

```bash
kubectl api-resources | grep -E 'applications|appprojects'
```

No Argo CD Application or AppProject resources were registered.

### Conclusion

The training component set was not a complete standalone Argo CD installation. The problem was not just one missing permission.

### Correction

I did not grant broad privileges to the Kubernetes `default` service account.

Instead, I:

1. inspected the official Argo CD v2.10.7 install manifest
2. confirmed it included the missing service accounts, RBAC resources, and CRDs
3. removed the partial Argo CD runtime resources
4. preserved the `argocd` namespace
5. applied the official pinned upstream manifest

### Validation

After the correction:

- all Argo CD control-plane pods were `1/1 Running`
- the expected dedicated service accounts existed
- `Application`, `ApplicationSet`, and `AppProject` CRDs were available

Evidence:

- `evidence/command-output/05-argocd-server-previous.log`
- `evidence/command-output/06-argocd-server-describe.txt`
- `evidence/command-output/07-argocd-rbac-crd-diagnosis.txt`
- `evidence/command-output/11-argocd-full-install-validation.txt`

---

## 2. Splunk image architecture on Apple Silicon

### Context

The GitOps Application reused the stateful Splunk manifests from Lab 01.

The host is Apple Silicon, while the Splunk image used by the lab is amd64.

### Splunk architecture correction

The image was preloaded inside the `argocd` Minikube VM using the amd64 platform:

```bash
minikube -p argocd ssh -- \
  'docker pull --platform linux/amd64 splunk/splunk:10.4.0'
```

Rosetta support was enabled for the Minikube profile.

### Splunk validation

The image reported:

```text
OS=linux
Architecture=amd64
```

and the Splunk workload synchronized successfully through Argo CD.

---

## 3. GitOps source versus runtime prerequisites

### Issue

The published Lab 01 manifests reference a Kubernetes Secret named `splunk-secret`.

The secret intentionally does not exist in Git.

### Approach

The secret was created at runtime in the destination cluster before Argo CD synchronized the workload.

This preserved the GitOps structure without committing a credential.

### Security note

No Splunk password value was saved in project evidence.

---

## 4. AppProject cross-environment destination test

### Goal

Verify that a prod-designated Argo CD project cannot be redirected to a dev namespace.

### Test

An intentionally invalid Application declared:

```text
project: splunk-prod
destination namespace: splunk-dev
```

### Result

Kubernetes accepted the Application custom resource, but Argo CD reported `InvalidSpecError` with a message explaining that `splunk-dev` did not match any destination allowed by the `splunk-prod` project.

### Interpretation

This distinguishes two layers:

```text
Kubernetes API validation
        |
        v
Is this a valid Application custom resource?

Argo CD AppProject policy
        |
        v
Is this Application allowed to deploy to that destination?
```

The negative test proved the second control was active.

Evidence:

- `tests/01-prod-wrong-destination.yaml`
- `evidence/screenshots/07-appproject-destination-policy-denied.png`

---

## 5. Local account versus production identity model

### Requirement

The instructor RBAC exercise referred to abstract `students` and `admins` groups.

The local lab did not have an external identity provider or SSO group claims configured.

### Adaptation

I created a local Argo CD account named `platform-operator` and mapped it directly to `role:nonprod-operator`.

The role permitted dev/test synchronization and denied prod-designated synchronization.

### Why

This made the exercise directly testable without claiming an SSO implementation that was not present.

In a production environment, the same role would typically be associated with an identity-provider group rather than a standalone local account.

---

## 6. `can-i` policy check versus real authorization test

### Initial validation

Authenticated as `platform-operator`:

```text
DEV sync:   yes
TEST sync:  yes
PROD sync:  no
```

This showed that the RBAC engine evaluated the intended policy.

### Stronger validation

I then created two Argo CD Applications using the same lightweight Git source:

- `rbac-demo-dev`
- `rbac-demo-prod`

As `platform-operator`:

- DEV synchronized successfully
- PROD returned `PermissionDenied`
- the PROD ConfigMap remained absent

After switching to `admin`:

- the same PROD Application synchronized successfully
- the ConfigMap was created

### RBAC interpretation

The failed prod-designated sync was an authorization decision, not an application, repository, or namespace failure.

Evidence:

- `evidence/command-output/19-argocd-rbac-validation.txt`
- `evidence/command-output/21-argocd-rbac-enforcement-validation.txt`
- `evidence/command-output/22-argocd-admin-prod-sync-validation.txt`

---

## 7. Argo CD CLI login reset the port-forward connection

### CLI login symptom

The Argo CD UI was reachable through:

```bash
kubectl -n argocd port-forward svc/argocd-server 9081:443
```

and HTTPS returned HTTP 200.

However, `argocd login` repeatedly caused the port-forward to terminate with errors including:

```text
Connection reset by peer
error: lost connection to pod
```

The Argo CD server pod remained `1/1 Running` with zero restarts.

### Initial possibilities

The host runs both Tailscale and Bitdefender. Both install macOS system or network extensions, so network filtering was a possible cause.

I did not disable either product immediately.

### Version check

The local Homebrew CLI was:

```text
argocd v3.5.1
```

The lab server was:

```text
quay.io/argoproj/argocd:v2.10.7
```

### CLI version correction

I installed a separate Apple Silicon Argo CD v2.10.7 CLI under:

```text
~/bin/argocd-v2.10.7/argocd
```

and retried the login against the same server and port-forward.

### CLI login result

The version-matched CLI logged in successfully:

```text
'admin:login' logged in successfully
```

### Lesson

The failure looked like a networking problem, but the first confirmed correction was aligning the CLI with the pinned server version.

Changing one variable at a time avoided unnecessarily disabling endpoint-security or overlay-network software.

---

## 8. Cleanup after authorization testing

The two temporary RBAC test Applications and their namespaces were deleted after validation:

```text
rbac-demo-dev
rbac-demo-prod
splunk-dev
splunk-prod
```

The manifests, screenshots, and command-output evidence were retained so the test remains reproducible and auditable.
