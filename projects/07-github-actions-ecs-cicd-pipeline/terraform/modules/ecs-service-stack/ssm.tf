resource "aws_ssm_parameter" "greeting" {
  # Plain String on purpose. This is the default greeting, not a secret.
  # CKV2_AWS_34 is recorded in docs/iac-scan-findings.md and is not skipped.
  name  = "/p07/${var.environment}/api/GREETING"
  type  = "String"
  value = "hello"

  # Terraform sets the initial value. After that, change it with
  # aws ssm put-parameter --overwrite and a new deployment (the Phase 4 SSM
  # proof). A later apply must not revert that value.
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "example_secret" {
  # checkov:skip=CKV_AWS_337: SecureString uses the AWS-managed aws/ssm key, not a customer-managed key.
  name  = "/p07/${var.environment}/api/EXAMPLE_SECRET"
  type  = "SecureString"
  value = "replace-me"

  # Placeholder only. Set the real value out of band so it never sits in code:
  #   aws ssm put-parameter --region us-east-1 \
  #     --name /p07/<environment>/api/EXAMPLE_SECRET \
  #     --value '...' --type SecureString --overwrite
  # ignore_changes keeps that overwrite across later applies.
  lifecycle {
    ignore_changes = [value]
  }
}
