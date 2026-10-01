resource "aws_lambda_function" "analyzer" {
  function_name = local.function_names.analyzer
  description   = "Normalizes WAF events and requests Bedrock analysis"

  role    = aws_iam_role.analyzer.arn
  handler = "waf_bedrock_analyzer.lambda_handler"
  runtime = "python3.12"

  filename         = data.archive_file.analyzer.output_path
  source_code_hash = data.archive_file.analyzer.output_base64sha256

  memory_size = 256
  timeout     = 300

  environment {
    variables = {
      BEDROCK_MODEL_ID = var.bedrock_model_id
      DYNAMODB_TABLE   = aws_dynamodb_table.waf_events.name
      LOOKBACK_MINUTES = tostring(var.analyzer_lookback_minutes)
      MAX_LOG_EVENTS   = tostring(var.max_log_events)
      WAF_LOG_GROUP    = aws_cloudwatch_log_group.waf.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.analyzer,
    aws_iam_role_policy.analyzer,
  ]
}
