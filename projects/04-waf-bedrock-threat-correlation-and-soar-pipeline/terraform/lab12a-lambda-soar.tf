# Pre-create the log group so Terraform controls its retention and lifecycle.
resource "aws_cloudwatch_log_group" "soar" {
  name              = "/aws/lambda/${local.name_prefix}-soar-response"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

# Package the single-file Python agent into the ZIP format Lambda requires.
data "archive_file" "soar" {
  type        = "zip"
  source_file = "${path.module}/../src/soar_response_agent.py"
  output_path = "${path.module}/soar-response-agent.zip"
}

resource "aws_lambda_function" "soar" {
  function_name = "${local.name_prefix}-soar-response"
  description   = "Processes correlated WAF findings through deterministic SOAR playbooks"

  role    = aws_iam_role.soar.arn
  handler = "soar_response_agent.lambda_handler"
  runtime = "python3.12"

  filename         = data.archive_file.soar.output_path
  source_code_hash = data.archive_file.soar.output_base64sha256

  memory_size = 256
  timeout     = 120

  environment {
    variables = {
      BEDROCK_MODEL_ID           = var.bedrock_model_id
      CORRELATION_FINDINGS_TABLE = aws_dynamodb_table.correlation_findings.name
      ENABLE_BEDROCK             = "true"
      SECURITY_INCIDENTS_TABLE   = aws_dynamodb_table.security_incidents.name
      SNS_TOPIC_ARN              = aws_sns_topic.soar_notifications.arn
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.soar,
    aws_iam_role_policy.soar,
  ]

  tags = local.common_tags
}
