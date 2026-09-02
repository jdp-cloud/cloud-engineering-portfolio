# Kubernetes Stateful Application Lab

A hands-on Kubernetes portfolio project that deploys Splunk Enterprise as a stateful workload on a local Minikube cluster.

The lab focuses on Kubernetes workload configuration, persistent storage, runtime secret handling, service access, and troubleshooting an amd64 container image on Apple Silicon.

## What I Implemented

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

- Apple Silicon Mac
- Minikube
- `vfkit` driver
- Rosetta-enabled Minikube profile for amd64 container execution
- Kubernetes `v1.35.1`
- Splunk Enterprise `10.4.0`
- kubectl

## Project Structure

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

The cleaned manifests under `manifests/` represent the deployment reproduced and validated for this portfolio.

## Kubernetes Resources

### Namespace

The workload runs in a dedicated namespace:

    splunk

### ConfigMap

The ConfigMap supplies non-sensitive Splunk startup settings, including license and terms acceptance.

### Secret

The administrator password is created at runtime and is not stored in a YAML manifest or committed to the repository.

Example:

    read -s "SPLUNK_PASSWORD?Enter Splunk password: "
    echo

    printf '%s' "$SPLUNK_PASSWORD" | \
    kubectl create secret generic splunk-secret \
      -n splunk \
      --from-file=SPLUNK_PASSWORD=/dev/stdin \
      --dry-run=client -o yaml | \
    kubectl apply -f -

    unset SPLUNK_PASSWORD

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

Create the namespace:

    kubectl apply -f manifests/01-namespace.yaml

Create the ConfigMap:

    kubectl apply -f manifests/02-configmap.yaml

Create the runtime Secret before deploying the StatefulSet.

Apply the Services:

    kubectl apply -f manifests/04-service.yaml

Apply the StatefulSet:

    kubectl apply -f manifests/03-statefulset.yaml

Check workload status:

    kubectl -n splunk get pods
    kubectl -n splunk get pvc
    kubectl -n splunk get svc
    kubectl -n splunk get endpointslice

## Apple Silicon Compatibility

The Splunk image used in this lab required amd64 execution, while the Minikube node was running on Apple Silicon.

A Rosetta-enabled Minikube profile was created with:

    minikube start \
      -p splunk \
      --driver=vfkit \
      --rosetta \
      --cpus=2 \
      --memory=6144 \
      --kubernetes-version=v1.35.1

amd64 execution was validated with:

    minikube -p splunk ssh -- \
      'docker run --rm --platform linux/amd64 alpine:3.20 uname -m'

Expected result:

    x86_64

The Splunk image was then explicitly pulled as amd64 inside the Minikube environment:

    minikube -p splunk ssh -- \
      'docker pull --platform linux/amd64 splunk/splunk:10.4.0'

Additional troubleshooting details are documented in `notes/troubleshooting.md`.

## Validation

### Workload Health

The final StatefulSet reached:

    NAME       READY   STATUS    RESTARTS
    splunk-0   1/1     Running   0

The persistent volume claim remained `Bound`, and the Splunk Service had a working endpoint.

### Persistent Storage

A marker file was written to the persistent mount:

    kubectl -n splunk exec splunk-0 -- \
      sh -c 'date -u > /opt/splunk/var/persistence-test.txt'

The pod was intentionally deleted:

    kubectl -n splunk delete pod splunk-0

After the StatefulSet recreated the pod, the marker remained available:

    kubectl -n splunk exec splunk-0 -- \
      cat /opt/splunk/var/persistence-test.txt

This confirmed that data stored on the persistent volume survived pod replacement.

### Application Access

The Splunk web interface was validated using port forwarding:

    kubectl -n splunk port-forward svc/splunk 18000:8000

The application was then accessed locally at:

    http://localhost:18000

The authenticated Splunk Enterprise interface remained available after the pod recreation and persistence test.

## Troubleshooting

The deployment required several debugging steps, including:

- correcting an invalid Kubernetes Secret reference
- diagnosing the lack of an ARM64 Splunk image
- validating amd64 execution through Rosetta
- configuring the Splunk container security context
- correcting `SPLUNK_HOME_OWNERSHIP_ENFORCEMENT`
- recreating a malformed runtime Secret
- validating the StatefulSet after pod recreation

See `notes/troubleshooting.md` for the detailed failure-and-resolution sequence.

## Evidence

Selected evidence is stored under:

    evidence/command-output/
    evidence/screenshots/

Key validation artifacts include:

- successful amd64 execution validation
- stable StatefulSet and PVC status
- authenticated Splunk web interface
- persistent data validation after pod recreation

## Project Origin

This lab was completed as part of instructor-led Kubernetes training and was independently reproduced, troubleshot, cleaned, and documented for this portfolio.

Instructor reference material was retained locally for provenance and is not included in this public project directory.

## Scope

This is a local Minikube portfolio lab, not a production deployment.

Ingress, TLS, high availability, external load balancing, and managed Kubernetes infrastructure are outside the validated scope of this version of the project.
