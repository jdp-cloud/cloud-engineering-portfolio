# Lambda service trust policy for the SOAR execution role.
data "aws_iam_policy_document" "soar_assume_role" {
  statement {
    sid     = "AllowLambdaService"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "soar" {
  name               = "${local.name_prefix}-soar-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.soar_assume_role.json

  tags = local.common_tags
}

# Least-privilege permissions mapped to the SOAR agent's responsibilities.
data "aws_iam_policy_document" "soar" {
  statement {
    sid    = "WriteFunctionLogs"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "${aws_cloudwatch_log_group.soar.arn}:*",
    ]
  }

  statement {
    sid    = "ReadAndUpdateFindings"
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:UpdateItem",
    ]

    resources = [
      aws_dynamodb_table.correlation_findings.arn,
    ]
  }

  statement {
    sid    = "ManageIncidentRecord"
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]

    resources = [
      aws_dynamodb_table.security_incidents.arn,
    ]
  }

  statement {
    sid     = "PublishSOARNotification"
    effect  = "Allow"
    actions = ["sns:Publish"]

    resources = [
      aws_sns_topic.soar_notifications.arn,
    ]
  }

  statement {
    sid     = "GenerateBedrockSummaries"
    effect  = "Allow"
    actions = ["bedrock:InvokeModel"]

    resources = var.bedrock_resource_arns
  }
}

resource "aws_iam_role_policy" "soar" {
  name   = "${local.name_prefix}-soar-lambda-policy"
  role   = aws_iam_role.soar.id
  policy = data.aws_iam_policy_document.soar.json
}
