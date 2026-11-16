#!/usr/bin/env bash
# Rejection cases for scripts/image-uri.sh.

set -euo pipefail

script=$(cd "$(dirname "$0")" && pwd)/image-uri.sh
registry=123456789012.dkr.ecr.us-east-1.amazonaws.com
digest=sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
failures=0

expect_uri() {
  local desc=$1
  local app=$2
  local want=$3
  local got
  if ! got=$("$script" "$registry" "$app" "$digest"); then
    echo "FAIL: ${desc} was rejected" >&2
    failures=$((failures + 1))
    return
  fi
  if [[ "$got" != "$want" ]]; then
    echo "FAIL: ${desc}" >&2
    echo "  got:  ${got}" >&2
    echo "  want: ${want}" >&2
    failures=$((failures + 1))
    return
  fi
  echo "ok: ${desc}"
}

expect_reject() {
  local desc=$1
  shift
  if "$script" "$@" >/dev/null 2>&1; then
    echo "FAIL: ${desc} was accepted" >&2
    failures=$((failures + 1))
    return
  fi
  echo "ok: rejected ${desc}"
}

expect_uri "api" api "${registry}/p07-api@${digest}"
expect_uri "web" web "${registry}/p07-web@${digest}"

expect_reject "missing digest" "$registry" api ""
expect_reject "non-sha256 digest" "$registry" api "sha512:${digest#sha256:}"
expect_reject "digest without sha256 prefix" "$registry" api "${digest#sha256:}"
expect_reject "short digest" "$registry" api "sha256:abcd"
expect_reject "app other than web or api" "$registry" worker "$digest"
expect_reject "empty app" "$registry" "" "$digest"
expect_reject "prefixed app name" "$registry" p07-api "$digest"
expect_reject "empty registry" "" api "$digest"

if [[ "$failures" -ne 0 ]]; then
  echo "${failures} failed" >&2
  exit 1
fi

echo "image-uri tests passed"
