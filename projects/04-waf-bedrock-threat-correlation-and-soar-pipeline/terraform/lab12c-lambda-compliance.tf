resource "aws_cloudwatch_log_group" "compliance" {
  name              = "/aws/lambda/${local.compliance_function_name}"
  retention_in_days = var.log_retention_days

  tags = merge(
    local.common_tags,
    {
      Lab     = "12C"
      Purpose = "Compliance agent logs"
    }
  )
}

data "archive_file" "compliance" {
  type        = "zip"
  output_path = "${path.module}/compliance-agent.zip"

  source {
    content  = file("${path.module}/../lambda/compliance.py")
    filename = "compliance.py"
  }

  source {
    content  = file("${path.module}/../json/controls.json")
    filename = "controls.json"
  }
}

resource "aws_lambda_function" "compliance" {
  function_name = local.compliance_function_name
  description   = "Evaluates operational security evidence against compliance controls"

  role    = aws_iam_role.compliance.arn
  handler = "compliance.lambda_handler"
  runtime = "python3.12"

  architectures = [
    "x86_64",
  ]

  filename         = data.archive_file.compliance.output_path
  source_code_hash = data.archive_file.compliance.output_base64sha256

  layers = [
    aws_lambda_layer_version.reportlab.arn,
  ]

  memory_size = 512
  timeout     = 120

  ephemeral_storage {
    size = 512
  }

  environment {
    variables = {
      # Required by compliance.py
      COMPLIANCE_EVIDENCE_TABLE = aws_dynamodb_table.compliance_evidence.name
      REPORT_BUCKET             = aws_s3_bucket.executive_reports.id

      # Reporting
      REPORT_PREFIX     = var.compliance_report_prefix
      REPORT_TITLE      = var.compliance_report_title
      ORGANIZATION_NAME = var.organization_name

      # Instructor control library resource resolution
      WAF_EVENTS_TABLE = aws_dynamodb_table.waf_events.name

      CORRELATION_FINDINGS_TABLE = (
        aws_dynamodb_table.correlation_findings.name
      )

      SECURITY_INCIDENTS_TABLE = (
        aws_dynamodb_table.security_incidents.name
      )

      EXECUTIVE_REPORT_PREFIX = var.report_prefix

      # Bedrock
      BEDROCK_MODEL_ID = var.bedrock_model_id
      ENABLE_BEDROCK   = tostring(var.enable_compliance_bedrock)

      # Instructor default behavior
      UNEVALUATED_STATUS = "REVIEW"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.compliance,
    aws_iam_role_policy.compliance,
    aws_s3_bucket_policy.executive_reports,
    aws_s3_bucket_server_side_encryption_configuration.executive_reports,
  ]

  tags = merge(
    local.common_tags,
    {
      Lab     = "12C"
      Purpose = "Compliance evidence evaluation"
    }
  )
}