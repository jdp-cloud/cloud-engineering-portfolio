resource "aws_cloudwatch_log_group" "checker" {
  name              = "/aws/lambda/${local.checker_name}"
  retention_in_days = 14
}
