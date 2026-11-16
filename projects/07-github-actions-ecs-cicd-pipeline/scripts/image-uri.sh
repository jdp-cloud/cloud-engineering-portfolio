#!/usr/bin/env bash
# Print registry/p07-<app>@<digest> after checking each argument.
#
# Usage: scripts/image-uri.sh <registry> <app> <digest>
#
# The registry is an ECR hostname (the account ID is in it). Callers mask that
# hostname before they run this script. Job outputs must stay bare digests.
# This script is for a step output inside one job.

set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: scripts/image-uri.sh <registry> <app> <digest>" >&2
  exit 2
fi

registry=$1
app=$2
digest=$3

if ! [[ "$registry" =~ ^[0-9]{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com$ ]]; then
  echo "registry must be an ECR hostname" >&2
  exit 1
fi

case "$app" in
  web|api) ;;
  *)
    echo "app must be web or api" >&2
    exit 1
    ;;
esac

if [[ -z "$digest" ]]; then
  echo "digest is empty" >&2
  exit 1
fi

if ! [[ "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "digest must be sha256 and 64 lowercase hex characters" >&2
  exit 1
fi

printf '%s\n' "${registry}/p07-${app}@${digest}"
