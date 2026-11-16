output "bucket_name" {
  description = "Synthetic eTMF bucket. Prefixes are incoming/, config/, and reports/."
  value       = aws_s3_bucket.etmf.bucket
}

output "checker_function_name" {
  description = "Lambda that runs on an incoming CSV upload and on the Monday schedule."
  value       = aws_lambda_function.checker.function_name
}

output "weekly_schedule" {
  description = "EventBridge Scheduler expression. The timezone is America/Chicago."
  value       = aws_scheduler_schedule.weekly.schedule_expression
}

output "budget_name" {
  description = "Monthly cost budget. The alarm goes to budget_alert_email."
  value       = aws_budgets_budget.monthly.name
}

output "sample_index_key" {
  description = "Synthetic index uploaded for the demo. Null when upload_sample_index is false."
  value       = var.upload_sample_index ? aws_s3_object.sample_index[0].key : null
}

output "classifier_function_name" {
  description = "Set only when enable_bedrock is true. The classifier never writes the index."
  value       = var.enable_bedrock ? aws_lambda_function.classifier[0].function_name : null
}
