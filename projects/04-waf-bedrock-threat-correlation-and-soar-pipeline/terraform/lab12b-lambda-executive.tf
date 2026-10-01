resource "aws_cloudwatch_log_group" "executive_dashboard" {
  name              = "/aws/lambda/${local.executive_dashboard_function_name}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

data "archive_file" "executive_dashboard" {
  type        = "zip"
  source_file = "${path.module}/../src/executive_dashboard_agent.py"
  output_path = "${path.module}/executive-dashboard-agent.zip"
}

resource "aws_lambda_layer_version" "reportlab" {
  filename         = "${path.module}/reportlab-python312-x86_64.zip"
  source_code_hash = filebase64sha256("${path.module}/reportlab-python312-x86_64.zip")

  layer_name          = "${local.name_prefix}-reportlab-python312"
  description         = "ReportLab 4.4.3 and dependencies for the Lab 12B executive-reporting Lambda"
  compatible_runtimes = ["python3.12"]

  compatible_architectures = [
    "x86_64",
  ]
}

resource "aws_lambda_function" "executive_dashboard" {
  function_name = local.executive_dashboard_function_name
  description   = "Generates synchronized executive PDF and JSON security reports"

  role    = aws_iam_role.executive_dashboard.arn
  handler = "executive_dashboard_agent.lambda_handler"
  runtime = "python3.12"

  architectures = [
    "x86_64",
  ]

  filename         = data.archive_file.executive_dashboard.output_path
  source_code_hash = data.archive_file.executive_dashboard.output_base64sha256

  layers = [
    aws_lambda_layer_version.reportlab.arn,
  ]

  memory_size = 1024
  timeout     = 120

  ephemeral_storage {
    size = 512
  }

  environment {
    variables = {
      BEDROCK_MODEL_ID           = var.bedrock_model_id
      CORRELATION_FINDINGS_TABLE = aws_dynamodb_table.correlation_findings.name
      ENABLE_BEDROCK             = tostring(var.enable_executive_bedrock)
      MAX_ITEMS_PER_TABLE        = tostring(var.max_items_per_table)
      ORGANIZATION_NAME          = var.organization_name
      REPORT_BUCKET              = aws_s3_bucket.executive_reports.id
      REPORT_PERIOD_HOURS        = tostring(var.report_period_hours)
      REPORT_PREFIX              = var.report_prefix
      REPORT_TITLE               = var.report_title
      SECURITY_INCIDENTS_TABLE   = aws_dynamodb_table.security_incidents.name
      WAF_EVENTS_TABLE           = aws_dynamodb_table.waf_events.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.executive_dashboard,
    aws_iam_role_policy.executive_dashboard,
    aws_s3_bucket_policy.executive_reports,
    aws_s3_bucket_server_side_encryption_configuration.executive_reports,
  ]

  tags = merge(
    local.common_tags,
    {
      Purpose = "Executive security reporting"
    }
  )
}
