resource "aws_lambda_function" "correlation" {
  function_name = local.function_names.correlation
  description   = "Correlates normalized WAF events into security findings"

  role    = aws_iam_role.correlation.arn
  handler = "waf_threat_correlation_agent.lambda_handler"
  runtime = "python3.12"

  filename         = data.archive_file.correlation.output_path
  source_code_hash = data.archive_file.correlation.output_base64sha256

  memory_size = 256
  timeout     = 120

  environment {
    variables = {
      ADMIN_URI_KEYWORDS         = join(",", var.admin_uri_keywords)
      BEDROCK_MODEL_ID           = var.bedrock_model_id
      CORRELATION_FINDINGS_TABLE = aws_dynamodb_table.correlation_findings.name
      CORRELATION_WINDOW_MINUTES = tostring(var.correlation_window_minutes)
      MAX_EVENTS                 = tostring(var.max_correlation_events)
      MINIMUM_EVENT_COUNT        = tostring(var.minimum_event_count)
      WAF_EVENTS_TABLE           = aws_dynamodb_table.waf_events.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.correlation,
    aws_iam_role_policy.correlation,
  ]
}
