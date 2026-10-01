resource "aws_iam_role" "compliance" {
  name               = "${local.name_prefix}-compliance-agent-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = merge(
    local.common_tags,
    {
      Lab     = "12C"
      Purpose = "Compliance agent execution role"
    }
  )
}

data "aws_iam_policy_document" "compliance" {

  # -------------------------------------------------------------
  # CloudWatch Logs
  # -------------------------------------------------------------

  statement {
    sid    = "WriteFunctionLogs"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "${aws_cloudwatch_log_group.compliance.arn}:*",
    ]
  }

  # -------------------------------------------------------------
  # Inspect Phase 1 DynamoDB tables for compliance controls
  # -------------------------------------------------------------

  statement {
    sid    = "ValidateDynamoDBControls"
    effect = "Allow"

    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:Scan",
    ]

    resources = [
      aws_dynamodb_table.waf_events.arn,
      aws_dynamodb_table.correlation_findings.arn,
      aws_dynamodb_table.security_incidents.arn,
    ]
  }

  # -------------------------------------------------------------
  # Read-only permissions for additional compliance validators
  # -------------------------------------------------------------

  statement {
    sid    = "ValidatorReadOnly"
    effect = "Allow"

    actions = [
      "events:DescribeRule",
      "scheduler:GetSchedule",
      "sns:GetTopicAttributes",
      "lambda:GetFunctionConfiguration",
    ]

    resources = ["*"]
  }

  # -------------------------------------------------------------
  # Save immutable compliance evidence
  # -------------------------------------------------------------

  statement {
    sid    = "WriteComplianceEvidence"
    effect = "Allow"

    actions = [
      "dynamodb:BatchWriteItem",
      "dynamodb:PutItem",
    ]

    resources = [
      aws_dynamodb_table.compliance_evidence.arn,
    ]
  }

  # -------------------------------------------------------------
  # Validate that executive reports exist
  # -------------------------------------------------------------

  statement {
    sid    = "ReadExecutiveReportEvidence"
    effect = "Allow"

    actions = [
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.executive_reports.arn,
    ]
  }

  # -------------------------------------------------------------
  # Publish compliance PDF and JSON reports
  # -------------------------------------------------------------

  statement {
    sid    = "WriteComplianceReports"
    effect = "Allow"

    actions = [
      "s3:PutObject",
    ]

    resources = [
      "${aws_s3_bucket.executive_reports.arn}/${var.compliance_report_prefix}/*",
    ]
  }

  # -------------------------------------------------------------
  # Bedrock narrative generation
  # -------------------------------------------------------------

  statement {
    sid    = "GenerateComplianceNarrative"
    effect = "Allow"

    actions = [
      "bedrock:InvokeModel",
    ]

    resources = var.bedrock_resource_arns
  }
}

resource "aws_iam_role_policy" "compliance" {
  name   = "${local.name_prefix}-compliance-agent-policy"
  role   = aws_iam_role.compliance.id
  policy = data.aws_iam_policy_document.compliance.json
}