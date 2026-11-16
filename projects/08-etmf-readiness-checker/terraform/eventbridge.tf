resource "aws_scheduler_schedule" "weekly" {
  name                         = "p08-etmf-weekly-check"
  description                  = "Re-check the latest synthetic eTMF index so expiry flags move with the calendar."
  schedule_expression          = "cron(0 7 ? * MON *)"
  schedule_expression_timezone = "America/Chicago"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.checker.arn
    role_arn = aws_iam_role.scheduler.arn
    input = jsonencode({
      source = "aws.scheduler"
      action = "check_latest"
    })
  }
}
