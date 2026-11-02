# Retention is 7 days on purpose. A longer retention would keep a short-lived
# lab's logs around. The one-year check is recorded in docs/iac-scan-findings.md.

resource "aws_cloudwatch_log_group" "web" {
  # checkov:skip=CKV_AWS_158: AWS-owned encryption. This lab does not use a customer-managed key.
  name              = "/p07/${var.environment}/web"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "api" {
  # checkov:skip=CKV_AWS_158: AWS-owned encryption. This lab does not use a customer-managed key.
  name              = "/p07/${var.environment}/api"
  retention_in_days = 7
}
