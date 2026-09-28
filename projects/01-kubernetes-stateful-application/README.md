# Kubernetes Stateful Application Lab

![Kubernetes](https://img.shields.io/badge/Kubernetes-v1.35.1-326CE5?logo=kubernetes&logoColor=white)
![Minikube](https://img.shields.io/badge/Minikube-vfkit%20%2B%20Rosetta-F5A623)
![Splunk](https://img.shields.io/badge/Splunk%20Enterprise-10.4.0-000000?logo=splunk&logoColor=white)
![Status](https://img.shields.io/badge/status-validated%20locally-brightgreen)

A hands-on Kubernetes portfolio project that deploys Splunk Enterprise as a stateful workload on a local Minikube cluster.

The lab focuses on workload configuration, persistent storage, runtime secret handling, service access, and troubleshooting an amd64 container image on Apple Silicon.

> **Scope:** This is a local Minikube portfolio lab, not a production deployment. See [Scope](#scope).

## At a glance

| | |
| --- | --- |
| **Problem** | Run a stateful, security-sensitive application on Kubernetes and prove its data survives pod replacement. |
| **Solution** | A single-replica StatefulSet with a persistent volume, a non-root security context, and an administrator password created at runtime instead of stored in Git. |
| **Environment** | Apple Silicon Mac, Minikube (`vfkit` driver, Rosetta), Kubernetes v1.35.1, Splunk Enterprise 10.4.0 |
| **Proof** | A marker file on the persistent volume survived deletion of the pod, and the authenticated Splunk UI stayed available afterwards. |
| **Hardest problem** | The Splunk image had no ARM64 build, so I enabled Rosetta and validated amd64 execution. |
| **Skills shown** | StatefulSets, PersistentVolumeClaims, Secrets, ConfigMaps, security contexts, Services, port-forwarding, systematic troubleshooting |

## Interview talk track

**Recruiter or hiring manager (30 seconds)**
"I deployed Splunk Enterprise on Kubernetes as a StatefulSet with persistent storage, then proved the data survives when the pod is deleted. The image only runs on amd64, and my laptop is Apple Silicon, so I had to work out the Rosetta setup and debug several configuration problems along the way. All of it is documented with command output and screenshots."

**Security engineer**
"The admin password is created at runtime and never committed to Git. The pod runs as a non-root user with a fixed UID and fsGroup. I kept the non-sensitive settings in a ConfigMap and the sensitive one in a Secret. It's a local lab, so I don't claim TLS, ingress or high availability."

## Contents

1. [What I implemented](#what-i-implemented)
2. [Environment](#environment)
3. [Project structure](#project-structure)
4. [Kubernetes resources](#kubernetes-resources)
5. [Deployment](#deployment)
6. [Apple Silicon compatibility](#apple-silicon-compatibility)
7. [Validation](#validation)
8. [Troubleshooting](#troubleshooting)
9. [Evidence](#evidence)
10. [Project origin](#project-origin)
11. [Scope](#scope)

## What I implemented

- Created a dedicated `splunk` namespace
- Managed non-sensitive application settings with a ConfigMap
- Created the Splunk administrator password as a Kubernetes Secret at runtime instead of storing it in source control
- Deployed Splunk Enterprise as a Kubernetes StatefulSet
- Configured a non-root pod security context using UID and GID `41812`
- Mounted persistent storage at `/opt/splunk/var`
- Created headless and ClusterIP Services for the stateful workload
- Validated the application through Kubernetes port forwarding
- Verified that persisted data survived pod deletion and StatefulSet recreation

## Environment

| Component | Configuration |
| --- | --- |
| Host | Apple Silicon Mac |
| Cluster | Minikube with the `vfkit` driver |
| amd64 support | Rosetta-enabled Minikube profile |
| Kubernetes | `v1.35.1` |
| Application | Splunk Enterprise `10.4.0` |
| Client | kubectl |

## Project structure

```text
.
├── README.md
├── manifests/
│   ├── 01-namespace.yaml
│   ├── 02-configmap.yaml
│   ├── 03-statefulset.yaml
│   └── 04-service.yaml
├── notes/
│   └── troubleshooting.md
├── evidence/
│   ├── command-output/
│   └── screenshots/
└── reference/
    └── instructor-current/
```

The cleaned manifests under `manifests/` represent the deployment reproduced and validated for this portfolio.

## Kubernetes resources

### Namespace

The workload runs in a dedicated namespace: `splunk`.

### ConfigMap

The ConfigMap supplies non-sensitive Splunk startup settings, including license and terms acceptance.

### Secret

The administrator password is created at runtime and is not stored in a YAML manifest or committed to the repository.

```bash
read -s "SPLUNK_PASSWORD?Enter Splunk password: "
echo

printf '%s' "$SPLUNK_PASSWORD" | \
kubectl create secret generic splunk-secret \
  -n splunk \
  --from-file=SPLUNK_PASSWORD=/dev/stdin \
  --dry-run=client -o yaml | \
kubectl apply -f -

unset SPLUNK_PASSWORD
```

### StatefulSet

The workload uses a single-replica StatefulSet with:

- Splunk Enterprise image `splunk/splunk:10.4.0`
- persistent storage mounted at `/opt/splunk/var`
- a `10Gi` volume claim
- `runAsUser: 41812`
- `fsGroup: 41812`
- `SPLUNK_HOME_OWNERSHIP_ENFORCEMENT=false`

### Services

Two Services support the workload:

- `splunk-headless` for StatefulSet identity
- `splunk` as a ClusterIP Service for application access

## Deployment

1. Create the namespace:

   ```bash
   kubectl apply -f manifests/01-namespace.yaml
   ```

2. Create the ConfigMap:

   ```bash
   kubectl apply -f manifests/02-configmap.yaml
   ```

3. Create the runtime Secret (see the [Secret](#secret) section) before deploying the StatefulSet.

4. Apply the Services:

   ```bash
   kubectl apply -f manifests/04-service.yaml
   ```

5. Apply the StatefulSet:

   ```bash
   kubectl apply -f manifests/03-statefulset.yaml
   ```

6. Check workload status:

   ```bash
   kubectl -n splunk get pods
   kubectl -n splunk get pvc
   kubectl -n splunk get svc
   kubectl -n splunk get endpointslice
   ```

## Apple Silicon compatibility

The Splunk image used in this lab required amd64 execution, while the Minikube node was running on Apple Silicon.

A Rosetta-enabled Minikube profile was created with:

```bash
minikube start \
  -p splunk \
  --driver=vfkit \
  --rosetta \
  --cpus=2 \
  --memory=6144 \
  --kubernetes-version=v1.35.1
```

amd64 execution was validated with:

```bash
minikube -p splunk ssh -- \
  'docker run --rm --platform linux/amd64 alpine:3.20 uname -m'
```

Expected result:

```text
x86_64
```

The Splunk image was then explicitly pulled as amd64 inside the Minikube environment:

```bash
minikube -p splunk ssh -- \
  'docker pull --platform linux/amd64 splunk/splunk:10.4.0'
```

Additional troubleshooting details are documented in [`notes/troubleshooting.md`](notes/troubleshooting.md).

## Validation

### Workload health

The final StatefulSet reached:

```text
NAME       READY   STATUS    RESTARTS
splunk-0   1/1     Running   0
```

The persistent volume claim remained `Bound`, and the Splunk Service had a working endpoint.

### Persistent storage

A marker file was written to the persistent mount:

```bash
kubectl -n splunk exec splunk-0 -- \
  sh -c 'date -u > /opt/splunk/var/persistence-test.txt'
```

The pod was intentionally deleted:

```bash
kubectl -n splunk delete pod splunk-0
```

After the StatefulSet recreated the pod, the marker remained available:

```bash
kubectl -n splunk exec splunk-0 -- \
  cat /opt/splunk/var/persistence-test.txt
```

This confirmed that data stored on the persistent volume survived pod replacement.

### Application access

The Splunk web interface was validated using port forwarding:

```bash
kubectl -n splunk port-forward svc/splunk 18000:8000
```

The application was then accessed locally at `http://localhost:18000`.

The authenticated Splunk Enterprise interface remained available after the pod recreation and persistence test.

## Troubleshooting

The deployment required several debugging steps:

| Problem | Resolution |
| --- | --- |
| Invalid Kubernetes Secret reference | Corrected the reference |
| No ARM64 Splunk image | Enabled Rosetta and validated amd64 execution |
| Container security context | Configured the Splunk security context (UID and GID `41812`) |
| `SPLUNK_HOME_OWNERSHIP_ENFORCEMENT` setting | Corrected the value |
| Malformed runtime Secret | Recreated the Secret |
| Behavior after pod replacement | Validated the StatefulSet after recreation |

See [`notes/troubleshooting.md`](notes/troubleshooting.md) for the detailed failure-and-resolution sequence.

## Evidence

Selected evidence is stored under `evidence/command-output/` and `evidence/screenshots/`.

Key validation artifacts include:

- successful amd64 execution validation
- stable StatefulSet and PVC status
- authenticated Splunk web interface
- persistent data validation after pod recreation

## Project origin

This lab was completed as part of instructor-led Kubernetes training and was independently reproduced, troubleshot, cleaned, and documented for this portfolio.

Instructor reference material was retained locally for provenance and is not included in this public project directory.

## Scope

This is a local Minikube portfolio lab, not a production deployment.

Ingress, TLS, high availability, external load balancing, and managed Kubernetes infrastructure are outside the validated scope of this version of the project.
