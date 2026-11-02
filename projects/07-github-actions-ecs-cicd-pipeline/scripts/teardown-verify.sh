#!/usr/bin/env bash
# Confirm Project 07 is gone from us-east-1 after terraform destroy.
#
# The GitHub OIDC provider for token.actions.githubusercontent.com is expected
# to remain. It is shared and pre-existing. This project never creates or
# manages it, and this script does not fail when it is still there.
#
# What should be gone: the p07-* roles, the p07-web and p07-api ECR
# repositories, and the environment stacks (VPCs, load balancers, ECS
# services, log groups, SSM parameters, budget).
#
# Usage: ./scripts/teardown-verify.sh
# Requires: AWS CLI v2 with credentials for the account that was used.

set -uo pipefail

REGION="us-east-1"
leftovers=0

# count <label> <aws command...>
# Prints an aligned line. A command failure counts as not clean.
count() {
  local label="$1"
  shift
  local out
  if ! out=$("$@" --output text 2>&1); then
    printf '  %-22s %s\n' "$label" "ERROR: ${out}"
    leftovers=$((leftovers + 1))
    return
  fi
  out=$(printf '%s' "$out" | tr -d '\r\n')
  printf '  %-22s %s\n' "$label" "$out"
  [[ "$out" != "0" ]] && leftovers=$((leftovers + 1))
}

echo "=== ${REGION} ==="

count "VPCs (project tag)" aws ec2 describe-vpcs --region "$REGION" \
  --filters Name=tag:Project,Values=p07-ecs-cicd \
  --query 'length(Vpcs)'

count "NAT gateways" aws ec2 describe-nat-gateways --region "$REGION" \
  --filter Name=tag:Project,Values=p07-ecs-cicd Name=state,Values=pending,available,deleting \
  --query 'length(NatGateways)'

# The backticks below are JMESPath literal syntax and must stay literal (SC2016).
# shellcheck disable=SC2016
count "Load balancers" aws elbv2 describe-load-balancers --region "$REGION" \
  --query 'length(LoadBalancers[?starts_with(LoadBalancerName, `p07-`)])'

# shellcheck disable=SC2016
count "ECS clusters" aws ecs list-clusters --region "$REGION" \
  --query 'length(clusterArns[?contains(@, `:cluster/p07-`)])'

service_count=0
service_error=0
for cluster in p07-staging p07-production; do
  # shellcheck disable=SC2016
  status=$(aws ecs describe-clusters --clusters "$cluster" --region "$REGION" \
    --query 'clusters[?status==`ACTIVE`].status | [0]' --output text 2>&1) || {
    printf '  %-22s %s\n' "ECS ${cluster}" "ERROR: ${status}"
    service_error=1
    continue
  }
  if [[ "$status" == "ACTIVE" ]]; then
    n=$(aws ecs list-services --cluster "$cluster" --region "$REGION" \
      --query 'length(serviceArns)' --output text 2>&1) || {
      printf '  %-22s %s\n' "ECS ${cluster}" "ERROR: ${n}"
      service_error=1
      continue
    }
    service_count=$((service_count + n))
  fi
done
if [[ "$service_error" -ne 0 ]]; then
  leftovers=$((leftovers + 1))
else
  printf '  %-22s %s\n' "ECS services" "$service_count"
  [[ "$service_count" -ne 0 ]] && leftovers=$((leftovers + 1))
fi

# shellcheck disable=SC2016
count "ECR p07-web/api" aws ecr describe-repositories --region "$REGION" \
  --query 'length(repositories[?repositoryName==`p07-web` || repositoryName==`p07-api`])'

count "Log groups /p07/" aws logs describe-log-groups --region "$REGION" \
  --log-group-name-prefix /p07/ \
  --query 'length(logGroups)'

count "SSM /p07/" aws ssm describe-parameters --region "$REGION" \
  --parameter-filters Key=Name,Option=BeginsWith,Values=/p07/ \
  --query 'length(Parameters)'

echo
echo "=== IAM roles ==="
roles=(
  p07-gha-staging-deploy
  p07-gha-production-deploy
  p07-gha-ecr-push
  p07-staging-ecs-execution
  p07-production-ecs-execution
)
for role in "${roles[@]}"; do
  err=$(aws iam get-role --role-name "$role" --query 'Role.RoleName' --output text 2>&1) && status=0 || status=$?
  if [[ "$status" -eq 0 ]]; then
    printf '  %-40s %s\n' "$role" "STILL PRESENT"
    leftovers=$((leftovers + 1))
  elif [[ "$err" == *"NoSuchEntity"* ]]; then
    printf '  %-40s %s\n' "$role" "absent"
  else
    printf '  %-40s %s\n' "$role" "ERROR: ${err}"
    leftovers=$((leftovers + 1))
  fi
done

echo
echo "=== Budget ==="
account=$(aws sts get-caller-identity --query Account --output text 2>&1) || {
  printf '  %-22s %s\n' "account" "ERROR: ${account}"
  leftovers=$((leftovers + 1))
  account=""
}
if [[ -n "$account" ]]; then
  err=$(aws budgets describe-budget --account-id "$account" --budget-name p07-ecs-cicd-monthly --query 'Budget.BudgetName' --output text 2>&1) && status=0 || status=$?
  if [[ "$status" -eq 0 ]]; then
    printf '  %-40s %s\n' "p07-ecs-cicd-monthly" "STILL PRESENT"
    leftovers=$((leftovers + 1))
  elif [[ "$err" == *"NotFound"* ]]; then
    printf '  %-40s %s\n' "p07-ecs-cicd-monthly" "absent"
  else
    printf '  %-40s %s\n' "p07-ecs-cicd-monthly" "ERROR: ${err}"
    leftovers=$((leftovers + 1))
  fi
fi

echo
echo "=== GitHub OIDC provider (expected to remain) ==="
# shellcheck disable=SC2016
oidc=$(aws iam list-open-id-connect-providers \
  --query 'OpenIDConnectProviderList[?ends_with(Arn, `/token.actions.githubusercontent.com`)].Arn' \
  --output text 2>&1) && oidc_status=0 || oidc_status=$?
if [[ "$oidc_status" -ne 0 ]]; then
  echo "  lookup failed: ${oidc}"
  echo "  This lookup is informational. It is not a leftover check."
elif [[ -n "$oidc" && "$oidc" != "None" ]]; then
  echo "  present (shared, not managed here): ${oidc}"
else
  echo "  not found. This project does not create it. Teardown does not require it to be gone."
fi
echo "  Not counted. Only the p07-* roles, ECR repositories, and environment stacks are removed."

echo
if [[ "$leftovers" -eq 0 ]]; then
  echo "CLEAN: no Project 07 resources found in ${REGION}. The OIDC provider may still be present."
else
  echo "NOT CLEAN: ${leftovers} check(s) need attention. Review the lines above."
  exit 1
fi
