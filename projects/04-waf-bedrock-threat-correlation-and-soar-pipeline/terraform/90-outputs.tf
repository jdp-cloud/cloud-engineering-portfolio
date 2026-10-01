output "api_invoke_url" {
  description = "Callable URL for the protected GET /analyze endpoint"
  value = join(
    "",
    [
      aws_api_gateway_stage.application.invoke_url,
      aws_api_gateway_resource.analyze.path,
    ]
  )
}

output "application_lambda_name" {
  description = "Protected application Lambda function name"
  value       = aws_lambda_function.application.function_name
}

output "analyzer_lambda_name" {
  description = "WAF analyzer Lambda function name"
  value       = aws_lambda_function.analyzer.function_name
}

output "correlation_lambda_name" {
  description = "Threat-correlation Lambda function name"
  value       = aws_lambda_function.correlation.function_name
}

output "waf_events_table_name" {
  description = "DynamoDB table containing normalized WAF events"
  value       = aws_dynamodb_table.waf_events.name
}

output "correlation_findings_table_name" {
  description = "DynamoDB table containing correlation findings"
  value       = aws_dynamodb_table.correlation_findings.name
}

output "waf_log_group_name" {
  description = "CloudWatch log group reserved for AWS WAF logs"
  value       = aws_cloudwatch_log_group.waf.name
}

output "web_acl_name" {
  description = "Name of the AWS WAF Web ACL protecting API Gateway"
  value       = aws_wafv2_web_acl.application.name
}

output "web_acl_arn" {
  description = "ARN of the AWS WAF Web ACL protecting API Gateway"
  value       = aws_wafv2_web_acl.application.arn
}

output "scheduler_schedule_group_name" {
  description = "EventBridge Scheduler group containing the Lab 12 schedules"
  value       = aws_scheduler_schedule_group.lab12.name
}

output "schedules_enabled" {
  description = "Whether automatic analyzer and correlation schedules are enabled"
  value       = var.enable_schedules
}

output "soar_lambda_name" {
  description = "Name of the Lab 12A SOAR response Lambda function"
  value       = aws_lambda_function.soar.function_name
}

output "security_incidents_table_name" {
  description = "Name of the Lab 12A security incidents DynamoDB table"
  value       = aws_dynamodb_table.security_incidents.name
}

output "soar_notifications_topic_arn" {
  description = "ARN of the standard SOAR notifications SNS topic"
  value       = aws_sns_topic.soar_notifications.arn
}

output "critical_alerts_topic_arn" {
  description = "ARN of the immediate critical alerts SNS topic"
  value       = aws_sns_topic.critical_alerts.arn
}

output "medium_high_event_rule_name" {
  description = "Name of the EventBridge rule routing MEDIUM and HIGH findings"
  value       = aws_cloudwatch_event_rule.medium_high_finding.name
}

output "critical_event_rule_name" {
  description = "Name of the EventBridge rule routing CRITICAL findings"
  value       = aws_cloudwatch_event_rule.critical_finding.name
}
