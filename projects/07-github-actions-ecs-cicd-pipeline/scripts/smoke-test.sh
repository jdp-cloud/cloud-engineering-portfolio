#!/usr/bin/env bash
# Hit the public ALB paths and check the version the two services report.
#
# Usage: scripts/smoke-test.sh <alb_dns> <expected_version>
#
# expected_version is the APP_VERSION of this deploy (v1.0.<run number>).
# Pass "any" to require only that /healthz and /api/health report the same
# version. The rollback workflow uses that, because the previous revision's
# version is not the tag that was just built.
#
# Retries cover the target-group deregistration delay: the service can be
# stable while the ALB still has a connection to the previous task.
# Each attempt waits up to 10 tries, 6 seconds apart.

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: scripts/smoke-test.sh <alb_dns> <expected_version>" >&2
  exit 2
fi

alb_dns=$1
expected=$2

if [[ -z "$alb_dns" || -z "$expected" ]]; then
  echo "alb_dns and expected_version are required" >&2
  exit 2
fi

if [[ "$alb_dns" == *"://"* || "$alb_dns" == */* ]]; then
  echo "pass the load balancer DNS name only, without a scheme or path" >&2
  exit 2
fi

fetch() {
  local path=$1
  local body_file=$2
  local code
  if ! code=$(curl -sS --max-time 15 -o "$body_file" -w '%{http_code}' "http://${alb_dns}${path}"); then
    : >"$body_file"
    code="000"
  fi
  printf '%s' "$code"
}

# Print the body that came back, then return 0 when this attempt passes.
check_attempt() {
  local hz_file=$1
  local api_file=$2
  local hello_file=$3
  local hz_code=$4
  local api_code=$5
  local hello_code=$6

  echo "GET /healthz HTTP ${hz_code}"
  cat "$hz_file"
  echo
  echo "GET /api/health HTTP ${api_code}"
  cat "$api_file"
  echo
  echo "GET /api/hello HTTP ${hello_code}"
  cat "$hello_file"
  echo

  python3 - "$expected" "$hz_code" "$api_code" "$hello_code" "$hz_file" "$api_file" "$hello_file" <<'PY'
import json
import sys

expected, hz_code, api_code, hello_code, hz_path, api_path, hello_path = sys.argv[1:8]

def load(label, code, path):
    raw = open(path, encoding="utf-8").read()
    if code != "200":
        raise SystemExit(f"{label} returned HTTP {code}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label} body is not JSON: {exc}")

healthz = load("/healthz", hz_code, hz_path)
api = load("/api/health", api_code, api_path)
hello = load("/api/hello", hello_code, hello_path)

for label, body in (("/healthz", healthz), ("/api/health", api)):
    if body.get("status") != "ok":
        raise SystemExit(f"{label} status is {body.get('status')!r}")
    version = body.get("version")
    if not isinstance(version, str) or version == "":
        raise SystemExit(f"{label} version is empty")

if expected == "any":
    if healthz["version"] != api["version"]:
        raise SystemExit(
            f"versions differ: /healthz {healthz['version']!r} /api/health {api['version']!r}"
        )
else:
    for label, body in (("/healthz", healthz), ("/api/health", api)):
        if body["version"] != expected:
            raise SystemExit(f"{label} version {body['version']!r} != {expected!r}")

message = hello.get("message")
if not isinstance(message, str) or message == "":
    raise SystemExit("/api/hello message is empty")
PY
}

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

attempt=1
while [[ "$attempt" -le 10 ]]; do
  echo "attempt ${attempt}"
  hz_code=$(fetch /healthz "${tmpdir}/healthz")
  api_code=$(fetch /api/health "${tmpdir}/api")
  hello_code=$(fetch /api/hello "${tmpdir}/hello")
  if check_attempt "${tmpdir}/healthz" "${tmpdir}/api" "${tmpdir}/hello" "$hz_code" "$api_code" "$hello_code"; then
    exit 0
  fi
  if [[ "$attempt" -lt 10 ]]; then
    sleep 6
  fi
  attempt=$((attempt + 1))
done

echo "smoke test failed after 10 attempts" >&2
exit 1
