#!/usr/bin/env bash
# Verify that nothing billable is left behind after `terraform destroy`.
# Checks the seven regions used by this project and prints a count per resource type.
# Exit code 0 = everything is clean. Exit code 1 = at least one resource remains.
#
# Usage: ./scripts/verify-teardown.sh
# Requires: AWS CLI v2 with credentials for the account that ran the deployment.

set -uo pipefail

REGIONS=(
  ap-northeast-1   # Tokyo (hub: SIEM, Aurora)
  ap-southeast-2   # Sydney
  us-west-1        # California
  eu-west-2        # London
  sa-east-1        # Sao Paulo
  ap-east-1        # Hong Kong (opt-in region)
  us-east-1        # New York
)

leftovers=0

# count <label> <aws command...>
# Runs the command, strips stray carriage returns and newlines, and prints an aligned line.
# Any failure (for example an opt-in error) prints ERROR and counts as not clean.
count() {
  local label="$1"; shift
  local out
  if ! out=$("$@" --output text 2>&1); then
    printf '  %-18s %s\n' "$label" "ERROR: ${out}"
    leftovers=$((leftovers + 1))
    return
  fi
  out=$(printf '%s' "$out" | tr -d '\r\n')
  printf '  %-18s %s\n' "$label" "$out"
  [[ "$out" != "0" ]] && leftovers=$((leftovers + 1))
}

for r in "${REGIONS[@]}"; do
  echo "=== ${r} ==="
  count "NAT gateways"    aws ec2 describe-nat-gateways --region "$r" \
    --filter Name=state,Values=pending,available,deleting \
    --query 'length(NatGateways)'
  count "Elastic IPs"     aws ec2 describe-addresses --region "$r" \
    --query 'length(Addresses)'
  count "Load balancers"  aws elbv2 describe-load-balancers --region "$r" \
    --query 'length(LoadBalancers)'
  # The backticks below are JMESPath literal syntax and must stay literal (SC2016).
  # shellcheck disable=SC2016
  count "Transit gateways" aws ec2 describe-transit-gateways --region "$r" \
    --query 'length(TransitGateways[?State!=`deleted`])'
  count "EC2 instances"   aws ec2 describe-instances --region "$r" \
    --filters Name=instance-state-name,Values=pending,running,stopping,stopped \
    --query 'length(Reservations[].Instances[])'
  count "Aurora clusters" aws rds describe-db-clusters --region "$r" \
    --query 'length(DBClusters)'
done

echo
if [[ "$leftovers" -eq 0 ]]; then
  echo "CLEAN: no billable resources found in any of the ${#REGIONS[@]} regions."
else
  echo "NOT CLEAN: ${leftovers} check(s) need attention. Review the lines above."
  exit 1
fi
