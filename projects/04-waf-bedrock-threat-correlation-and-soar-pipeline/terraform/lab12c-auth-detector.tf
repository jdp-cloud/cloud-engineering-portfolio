# ============================================================
# Lab F Enhancement: Unused Token Detector
# ============================================================
#
# The detector scans token-use telemetry for records that remain
# unused beyond the configured threshold. Alerts are emitted as
# structured CloudWatch Logs events.
# ============================================================

resource "aws_cloudwatch_log_group" "unused_token_detector" {
  name              = "/aws/lambda/${local.name_prefix}-unused-token-detector"
  retention_in_days = var.log_retention_days
}

resource "aws_iam_role" "unused_token_detector" {
  name        = "${local.name_prefix}-unused-token-detector-role"
  description = "Execution role for the Lab 12C unused-token detector"

  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "unused_token_detector" {
  statement {
    sid = "WriteDetectorLogs"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "${aws_cloudwatch_log_group.unused_token_detector.arn}:*",
    ]
  }

  statement {
    sid = "ScanTokenTelemetry"

    actions = [
      "dynamodb:Scan",
    ]

    resources = [
      aws_dynamodb_table.token_tracking.arn,
    ]
  }
}

resource "aws_iam_role_policy" "unused_token_detector" {
  name   = "${local.name_prefix}-unused-token-detector-policy"
  role   = aws_iam_role.unused_token_detector.name
  policy = data.aws_iam_policy_document.unused_token_detector.json
}

data "archive_file" "unused_token_detector" {
  type        = "zip"
  output_path = "${path.module}/unused-token-detector.zip"

  source {
    content = file(
      "${path.module}/../src/unused_token_detector.py"
    )

    filename = "unused_token_detector.py"
  }
}

resource "aws_lambda_function" "unused_token_detector" {
  function_name = "${local.name_prefix}-unused-token-detector"
  description   = "Detects unused token-tracking records older than the alert threshold"

  role    = aws_iam_role.unused_token_detector.arn
  handler = "unused_token_detector.lambda_handler"
  runtime = "python3.12"

  filename         = data.archive_file.unused_token_detector.output_path
  source_code_hash = data.archive_file.unused_token_detector.output_base64sha256

  memory_size = 128
  timeout     = 30

  environment {
    variables = {
      TOKEN_TABLE_NAME    = aws_dynamodb_table.token_tracking.name
      ALERT_AFTER_MINUTES = "10"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.unused_token_detector,
    aws_iam_role_policy.unused_token_detector,
  ]
}

# ============================================================
# EventBridge Scheduler
# ============================================================
#
# The unused-token detector runs every five minutes when Lab 12C
# schedules are enabled. It reuses the existing scheduler group
# and least-privilege scheduler execution role.
# ============================================================

resource "aws_scheduler_schedule" "unused_token_check" {
  name        = "${local.name_prefix}-unused-token-check"
  group_name  = aws_scheduler_schedule_group.lab12.name
  description = "Checks for unused token records older than the alert threshold"

  schedule_expression          = "rate(5 minutes)"
  schedule_expression_timezone = "UTC"
  state                        = var.enable_schedules ? "ENABLED" : "DISABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.unused_token_detector.arn
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      source = "eventbridge-scheduler"
      task   = "check-unused-tokens"
    })

    retry_policy {
      maximum_event_age_in_seconds = 3600
      maximum_retry_attempts       = 2
    }
  }

  depends_on = [
    aws_iam_role_policy.scheduler,
  ]
}
