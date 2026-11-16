resource "aws_budgets_budget" "monthly" {
  name         = "08-etmf-readiness-checker"
  budget_type  = "COST"
  limit_amount = "5"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  # The budget repeats from this start. It does not end.
  time_period_start = "2026-11-01_00:00"

  cost_filter {
    name = "TagKeyValue"
    values = [
      "user:Project$08-etmf-readiness-checker",
    ]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_alert_email]
  }
}
