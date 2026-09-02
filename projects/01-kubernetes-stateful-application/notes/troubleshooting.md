# Troubleshooting Notes

This project was built and validated locally on an Apple Silicon Mac using Minikube with the `vfkit` driver. Several issues surfaced during deployment, mainly around container architecture compatibility, Splunk startup behavior, and Kubernetes configuration.

## 1. amd64 Container Image on Apple Silicon

### Architecture Mismatch

The Minikube node was running on ARM64, while the Splunk Enterprise container image used for this lab was available as an amd64 image.

The initial image pull failed with an architecture mismatch:

    no matching manifest for linux/arm64/v8

An initial attempt to execute an amd64 container also resulted in:

    exec /bin/uname: exec format error

### Rosetta-Enabled Minikube Profile

A new Minikube profile was created using the `vfkit` driver with Rosetta enabled:

    minikube start \
      -p splunk \
      --driver=vfkit \
      --rosetta \
      --cpus=2 \
      --memory=6144 \
      --kubernetes-version=v1.35.1

amd64 execution was then validated inside the Minikube VM:

    minikube -p splunk ssh -- \
      'docker run --rm --platform linux/amd64 alpine:3.20 uname -m'

Result:

    x86_64

The Splunk image was explicitly pulled as amd64:

    minikube -p splunk ssh -- \
      'docker pull --platform linux/amd64 splunk/splunk:10.4.0'

The StatefulSet uses:

    imagePullPolicy: IfNotPresent

so Kubernetes can use the locally cached image.

## 2. Invalid Kubernetes Secret Reference

### Invalid Secret Name

The first StatefulSet definition contained a trailing period in the Secret name:

    name: splunk-secret.

Kubernetes rejected the resource because the name violated RFC 1123 naming requirements.

### Corrected Secret Reference

The Secret reference was corrected to:

    name: splunk-secret

The manifest was then reapplied successfully.

## 3. Splunk Startup and Container Security Context

### Splunk Startup Failure

After resolving the image architecture issue, the Splunk container progressed further but failed during its Ansible-based startup process.

The container encountered errors involving `sudo` while running under Rosetta.

### Security Context Configuration

The pod was configured to run using the UID and GID used by the unprivileged Splunk user:

    securityContext:
      runAsUser: 41812
      fsGroup: 41812

The container was also configured with:

    - name: SPLUNK_HOME_OWNERSHIP_ENFORCEMENT
      value: "false"

An earlier configuration accidentally supplied an incorrect value for this variable, which caused Splunk's startup process to continue attempting ownership changes.

Correcting the value allowed the startup sequence to progress.

## 4. Incorrect Runtime Secret Value

### Password Hashing Failure

Splunk later failed while attempting to hash the administrator password.

The logs revealed that the Kubernetes Secret contained a shell command instead of the intended password:

    kubectl apply -f manifests/04-service.yaml

This occurred because command text had been entered while the terminal was waiting for hidden password input.

### Runtime Secret Recreation

The Secret was recreated without storing the password in a YAML file:

    read -s "SPLUNK_PASSWORD?Enter Splunk password: "
    echo

    printf '%s' "$SPLUNK_PASSWORD" | \
    kubectl create secret generic splunk-secret \
      -n splunk \
      --from-file=SPLUNK_PASSWORD=/dev/stdin \
      --dry-run=client -o yaml | \
    kubectl apply -f -

    unset SPLUNK_PASSWORD

The Secret was verified using:

    kubectl -n splunk describe secret splunk-secret

The pod was then recreated so the updated environment variable would be loaded.

After this correction, the StatefulSet reached:

    READY   STATUS    RESTARTS
    1/1     Running   0

## 5. Persistent Storage Validation

A marker file was created inside the persistent Splunk volume:

    kubectl -n splunk exec splunk-0 -- \
      sh -c 'date -u > /opt/splunk/var/persistence-test.txt'

The pod was then intentionally deleted:

    kubectl -n splunk delete pod splunk-0

The StatefulSet recreated the pod automatically.

After recreation, the same PVC remained bound and the marker file was still present:

    kubectl -n splunk exec splunk-0 -- \
      cat /opt/splunk/var/persistence-test.txt

This confirmed that application data stored under `/opt/splunk/var` survived pod replacement.

## Final Validation

The completed local deployment was validated by confirming:

- `splunk-0` remained `1/1 Running` with zero restarts
- the persistent volume claim remained `Bound`
- the Kubernetes Service had a working endpoint
- data persisted after pod deletion and recreation
- the Splunk Enterprise web interface remained accessible through port forwarding

Local access was established with:

    kubectl -n splunk port-forward svc/splunk 18000:8000

and the application was accessed at:

    http://localhost:18000
