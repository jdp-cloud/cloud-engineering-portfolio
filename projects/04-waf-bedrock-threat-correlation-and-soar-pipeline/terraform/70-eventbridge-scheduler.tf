resource "aws_scheduler_schedule_group" "lab12" {
  name = "${local.name_prefix}-schedules"
}

resource "aws_scheduler_schedule" "analyzer" {
  name        = "${local.name_prefix}-analyzer"
  group_name  = aws_scheduler_schedule_group.lab12.name
  description = "Periodically reads and analyzes recent AWS WAF events"

  schedule_expression = var.analyzer_schedule_expression
  state               = var.enable_schedules ? "ENABLED" : "DISABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.analyzer.arn
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      source = "eventbridge-scheduler"
      task   = "analyze-waf-events"
    })

    # The analyzer is not fully end-to-end retryable after its
    # DynamoDB write, so automatic retries are disabled.
    retry_policy {
      maximum_event_age_in_seconds = 300
      maximum_retry_attempts       = 0
    }
  }

  depends_on = [
    aws_iam_role_policy.scheduler,
  ]
}

resource "aws_scheduler_schedule" "correlation" {
  name        = "${local.name_prefix}-correlation"
  group_name  = aws_scheduler_schedule_group.lab12.name
  description = "Periodically correlates normalized WAF events"

  schedule_expression = var.correlation_schedule_expression
  state               = var.enable_schedules ? "ENABLED" : "DISABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.correlation.arn
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      source = "eventbridge-scheduler"
      task   = "correlate-waf-events"
    })

    # Correlation currently creates UUID finding IDs, so retries
    # could produce duplicate findings.
    retry_policy {
      maximum_event_age_in_seconds = 900
      maximum_retry_attempts       = 0
    }
  }

  depends_on = [
    aws_iam_role_policy.scheduler,
  ]
}
