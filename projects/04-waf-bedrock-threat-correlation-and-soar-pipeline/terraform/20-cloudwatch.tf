# AWS WAF requires CloudWatch destination names to begin with
# aws-waf-logs-. The Web ACL logging configuration is added later.
resource "aws_cloudwatch_log_group" "waf" {
  name              = "aws-waf-logs-${local.name_prefix}"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "analyzer" {
  name              = "/aws/lambda/${local.function_names.analyzer}"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "correlation" {
  name              = "/aws/lambda/${local.function_names.correlation}"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/lambda/${local.function_names.application}"
  retention_in_days = var.log_retention_days
}
