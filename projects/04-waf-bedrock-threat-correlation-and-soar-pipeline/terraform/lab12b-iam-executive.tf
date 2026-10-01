resource "aws_iam_role" "executive_dashboard" {
  name               = "${local.name_prefix}-executive-dashboard-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = local.common_tags
}

data "aws_iam_policy_document" "executive_dashboard" {
  statement {
    sid    = "WriteFunctionLogs"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "${aws_cloudwatch_log_group.executive_dashboard.arn}:*",
    ]
  }

  statement {
    sid     = "ReadSecurityReportingData"
    effect  = "Allow"
    actions = ["dynamodb:Scan"]

    resources = [
      aws_dynamodb_table.waf_events.arn,
      aws_dynamodb_table.correlation_findings.arn,
      aws_dynamodb_table.security_incidents.arn,
    ]
  }

  statement {
    sid     = "GenerateExecutiveNarrative"
    effect  = "Allow"
    actions = ["bedrock:InvokeModel"]

    resources = var.bedrock_resource_arns
  }

  statement {
    sid     = "WriteExecutiveReports"
    effect  = "Allow"
    actions = ["s3:PutObject"]

    resources = [
      "${aws_s3_bucket.executive_reports.arn}/${var.report_prefix}/*",
    ]
  }
}

resource "aws_iam_role_policy" "executive_dashboard" {
  name   = "${local.name_prefix}-executive-dashboard-policy"
  role   = aws_iam_role.executive_dashboard.id
  policy = data.aws_iam_policy_document.executive_dashboard.json
}
