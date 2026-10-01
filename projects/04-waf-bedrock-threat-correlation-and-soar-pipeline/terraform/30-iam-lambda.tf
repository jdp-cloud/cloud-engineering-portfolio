data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    sid     = "LambdaAssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# ============================================================
# Analyzer execution role
# ============================================================

resource "aws_iam_role" "analyzer" {
  name               = "${local.name_prefix}-analyzer-role"
  description        = "Execution role for the Lab 12 WAF analyzer"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "analyzer" {
  statement {
    sid = "WriteAnalyzerLogs"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "${aws_cloudwatch_log_group.analyzer.arn}:*",
    ]
  }

  statement {
    sid = "ReadWAFLogs"

    actions = [
      "logs:FilterLogEvents",
    ]

    resources = [
      "${aws_cloudwatch_log_group.waf.arn}:*",
    ]
  }

  statement {
    sid = "StoreNormalizedWAFEvents"

    actions = [
      "dynamodb:PutItem",
    ]

    resources = [
      aws_dynamodb_table.waf_events.arn,
    ]
  }

  statement {
    sid = "InvokeBedrockModel"

    actions = [
      "bedrock:InvokeModel",
    ]

    resources = var.bedrock_resource_arns
  }
}

resource "aws_iam_role_policy" "analyzer" {
  name   = "${local.name_prefix}-analyzer-policy"
  role   = aws_iam_role.analyzer.name
  policy = data.aws_iam_policy_document.analyzer.json
}

# ============================================================
# Correlation execution role
# ============================================================

resource "aws_iam_role" "correlation" {
  name               = "${local.name_prefix}-correlation-role"
  description        = "Execution role for the Lab 12 correlation agent"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "correlation" {
  statement {
    sid = "WriteCorrelationLogs"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "${aws_cloudwatch_log_group.correlation.arn}:*",
    ]
  }

  statement {
    sid = "ReadNormalizedWAFEvents"

    actions = [
      "dynamodb:Scan",
    ]

    resources = [
      aws_dynamodb_table.waf_events.arn,
    ]
  }

  statement {
    sid = "StoreCorrelationFindings"

    actions = [
      "dynamodb:PutItem",
    ]

    resources = [
      aws_dynamodb_table.correlation_findings.arn,
    ]
  }

  statement {
    sid = "PublishThreatFindingEvents"

    actions = [
      "events:PutEvents",
    ]

    resources = [
      data.aws_cloudwatch_event_bus.default.arn,
    ]
  }

  statement {
    sid = "InvokeBedrockModel"

    actions = [
      "bedrock:InvokeModel",
    ]

    resources = var.bedrock_resource_arns
  }
}

resource "aws_iam_role_policy" "correlation" {
  name   = "${local.name_prefix}-correlation-policy"
  role   = aws_iam_role.correlation.name
  policy = data.aws_iam_policy_document.correlation.json
}

# ============================================================
# Protected application execution role
# ============================================================

resource "aws_iam_role" "application" {
  name               = "${local.name_prefix}-application-role"
  description        = "Execution role for the Lab 12 protected API Lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "application" {
  statement {
    sid = "WriteApplicationLogs"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "${aws_cloudwatch_log_group.application.arn}:*",
    ]
  }

  statement {
    sid = "UpdateTokenUsage"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:UpdateItem",
    ]

    resources = [
      aws_dynamodb_table.token_tracking.arn,
    ]
  }
}

resource "aws_iam_role_policy" "application" {
  name   = "${local.name_prefix}-application-policy"
  role   = aws_iam_role.application.name
  policy = data.aws_iam_policy_document.application.json
}

# ============================================================
# EventBridge Scheduler execution role
# ============================================================

data "aws_iam_policy_document" "scheduler_assume_role" {
  statement {
    sid     = "AllowEventBridgeSchedulerAssumeRole"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler" {
  name        = "${local.name_prefix}-scheduler-role"
  description = "Allows EventBridge Scheduler to invoke Lab 12 Lambda functions"

  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role.json
}

data "aws_iam_policy_document" "scheduler" {
  statement {
    sid     = "InvokeScheduledLambdaFunctions"
    actions = ["lambda:InvokeFunction"]

    resources = [
      aws_lambda_function.analyzer.arn,
      aws_lambda_function.correlation.arn,
      aws_lambda_function.unused_token_detector.arn,
    ]
  }
}

resource "aws_iam_role_policy" "scheduler" {
  name   = "${local.name_prefix}-scheduler-policy"
  role   = aws_iam_role.scheduler.name
  policy = data.aws_iam_policy_document.scheduler.json
}
