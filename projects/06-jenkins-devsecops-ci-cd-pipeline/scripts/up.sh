#!/usr/bin/env bash
# Start the lab.
#
# Passwords are generated here, handed to Docker Compose as environment variables, and shown once
# on the terminal. They are never written to a file in this repository.
#
# Optional environment variables:
#   SHOW_PASSWORDS=0     do not print the passwords at the end
#   CREDENTIALS_OUT=PATH also write them to PATH (mode 0600). The path must be OUTSIDE this repository.
#
# Optional Snyk dependency stage and Jira ticket on failure (off unless all six values are present):
#   op run --env-file=jenkins/.env.op -- ./scripts/up.sh
# The values come from 1Password through `op run`, are handed to Docker Compose as secrets (files under
# /run/secrets in the Jenkins container) and are never written to a file or printed by this script.
# Started any other way, the lab is exactly the 12-stage lab.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)"

die() { echo "error: $*" >&2; exit 1; }
for tool in docker curl openssl; do command -v "$tool" >/dev/null || die "$tool is required"; done
docker info >/dev/null 2>&1 || die "the Docker daemon is not running"

if [ -n "${CREDENTIALS_OUT:-}" ]; then
  out_dir="$(cd "$(dirname "$CREDENTIALS_OUT")" && pwd -P)"
  case "$out_dir/" in "$REPO_ROOT"/*) die "CREDENTIALS_OUT must be outside the repository" ;; esac
fi

gen() { openssl rand -hex 16; }
# SonarQube's password policy needs an upper-case letter, a lower-case letter, a digit and a symbol.
gen_complex() { printf 'Aa1-%s' "$(openssl rand -hex 14)"; }
export JENKINS_ADMIN_PASSWORD="$(gen)" SONAR_ADMIN_PASSWORD="$(gen_complex)" SONAR_DB_PASSWORD="$(gen)"
# Compose needs a value to parse the file; the real token replaces this once SonarQube is up.
export SONAR_TOKEN="placeholder"

# Optional integrations: all six values present = enabled, none = off, anything in between is a mistake.
# Only the NAMES of missing variables are ever printed, never a value.
integration_vars=(SNYK_TOKEN SNYK_ORG JIRA_API_TOKEN JIRA_EMAIL JIRA_SITE_URL JIRA_PROJECT_KEY)
present=0; missing=""; unresolved=""
for name in "${integration_vars[@]}"; do
  if [ -n "${!name:-}" ]; then
    present=$((present + 1))
    case "${!name}" in op://*) unresolved="$unresolved $name" ;; esac
  else
    missing="$missing $name"
  fi
done
if [ -n "$unresolved" ]; then
  die "still an op:// reference:$unresolved. Start with: op run --env-file=jenkins/.env.op -- ./scripts/up.sh"
elif [ "$present" -eq "${#integration_vars[@]}" ]; then
  export COMPOSE_FILE="docker-compose.yml:docker-compose.integrations.yml"
  INTEGRATIONS=on
elif [ "$present" -eq 0 ]; then
  INTEGRATIONS=off
else
  die "the Snyk and Jira values are only partly set. Missing:$missing"
fi
echo "==> Optional Snyk and Jira stages: $INTEGRATIONS"

SONAR_URL="http://127.0.0.1:9000"
JENKINS_URL="http://127.0.0.1:8080"

# POST to the SonarQube API and print the server's error message if it refuses (plain `curl -f` hides it).
sonar_post() {
  local user="$1" endpoint="$2"; shift 2
  local body code
  body="$(mktemp)"
  code="$(curl -sS -o "$body" -w '%{http_code}' -u "$user" -X POST "$SONAR_URL$endpoint" "$@")"
  case "$code" in
    2??) cat "$body"; rm -f "$body" ;;
    *) echo "SonarQube $endpoint failed with HTTP $code: $(cat "$body")" >&2; rm -f "$body"; exit 1 ;;
  esac
}

echo "==> Starting Postgres and SonarQube (the first start takes a minute or two)"
docker compose up -d --wait postgres sonarqube

echo "==> Configuring SonarQube: admin password, project, analysis token, quality-gate webhook"
sonar_post "admin:admin" /api/users/change_password \
  --data-urlencode "login=admin" --data-urlencode "previousPassword=admin" \
  --data-urlencode "password=$SONAR_ADMIN_PASSWORD" >/dev/null
sonar_post "admin:$SONAR_ADMIN_PASSWORD" /api/projects/create \
  -d "name=sample-app" -d "project=sample-app" >/dev/null
# A strict gate on OVERALL code: no open issues, coverage of at least 80%, every security hotspot reviewed.
# (The built-in "Sonar way" gate only looks at new code, so an issue on the first analysis never fails it.)
sonar_post "admin:$SONAR_ADMIN_PASSWORD" /api/qualitygates/create -d "name=strict-overall" >/dev/null
sonar_post "admin:$SONAR_ADMIN_PASSWORD" /api/qualitygates/create_condition \
  -d "gateName=strict-overall" -d "metric=violations" -d "op=GT" -d "error=0" >/dev/null
sonar_post "admin:$SONAR_ADMIN_PASSWORD" /api/qualitygates/create_condition \
  -d "gateName=strict-overall" -d "metric=coverage" -d "op=LT" -d "error=80" >/dev/null
sonar_post "admin:$SONAR_ADMIN_PASSWORD" /api/qualitygates/create_condition \
  -d "gateName=strict-overall" -d "metric=security_hotspots_reviewed" -d "op=LT" -d "error=100" >/dev/null
sonar_post "admin:$SONAR_ADMIN_PASSWORD" /api/qualitygates/select \
  -d "gateName=strict-overall" -d "projectKey=sample-app" >/dev/null
SONAR_TOKEN="$(sonar_post "admin:$SONAR_ADMIN_PASSWORD" /api/user_tokens/generate \
  -d "name=jenkins" | sed -n 's/.*"token":"\([^"]*\)".*/\1/p')"
[ -n "$SONAR_TOKEN" ] || die "could not create the SonarQube token"
export SONAR_TOKEN
sonar_post "admin:$SONAR_ADMIN_PASSWORD" /api/webhooks/create \
  -d "name=jenkins" --data-urlencode "url=http://jenkins:8080/sonarqube-webhook/" >/dev/null

echo "==> Building and starting Jenkins and the Docker-in-Docker sidecar"
docker compose up -d --build dind jenkins
printf "==> Waiting for Jenkins "
for _ in $(seq 1 90); do
  if curl -fsS -o /dev/null "$JENKINS_URL/login"; then break; fi
  printf "."; sleep 3
done
echo
curl -fsS -o /dev/null "$JENKINS_URL/login" || die "Jenkins did not become ready; run: docker compose logs jenkins"

if [ -n "${CREDENTIALS_OUT:-}" ]; then
  umask 077
  {
    echo "JENKINS_ADMIN_PASSWORD=$JENKINS_ADMIN_PASSWORD"
    echo "SONAR_ADMIN_PASSWORD=$SONAR_ADMIN_PASSWORD"
  } > "$CREDENTIALS_OUT"
fi

echo
echo "Jenkins    $JENKINS_URL   user: admin"
echo "SonarQube  $SONAR_URL   user: admin"
if [ "${SHOW_PASSWORDS:-1}" = "1" ]; then
  echo "Jenkins password:    $JENKINS_ADMIN_PASSWORD"
  echo "SonarQube password:  $SONAR_ADMIN_PASSWORD"
  echo "These are shown once. They are not stored anywhere in this repository."
fi
echo "Run the job 'sample-app-devsecops' with BRANCH=main (passes) or BRANCH=vulnerable-demo (a gate blocks it)."
if [ "$INTEGRATIONS" = "on" ]; then
  echo "Tick RUN_SNYK_JIRA to add the Snyk gate and a Jira ticket on failure."
fi
