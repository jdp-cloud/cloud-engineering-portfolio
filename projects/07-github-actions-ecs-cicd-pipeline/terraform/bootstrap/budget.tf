resource "aws_budgets_budget" "p07" {
  name         = "p07-ecs-cicd-monthly"
  budget_type  = "COST"
  limit_amount = "10"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  # Fixed start so later plans do not drift. The AWS Budgets API key for a
  # cost allocation tag is TagKeyValue, and the value is user:<key>$<value>.
  # Confirm the filter on the first plan.
  time_period_start = "2026-11-01_00:00"

  cost_filter {
    name = "TagKeyValue"
    values = [
      "user:Project$p07-ecs-cicd",
    ]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_alert_email]
  }
}
