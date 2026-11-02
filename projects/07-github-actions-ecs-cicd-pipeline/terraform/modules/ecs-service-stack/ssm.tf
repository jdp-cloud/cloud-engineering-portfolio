resource "aws_ssm_parameter" "greeting" {
  # Plain String on purpose. This is the default greeting, not a secret.
  # CKV2_AWS_34 is recorded in docs/iac-scan-findings.md and is not skipped.
  name  = "/p07/${var.environment}/api/GREETING"
  type  = "String"
  value = "hello"
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
