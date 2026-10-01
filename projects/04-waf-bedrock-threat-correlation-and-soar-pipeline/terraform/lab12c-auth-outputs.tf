# ============================================================
# Lab D/E/F Authentication and Authorization Outputs
# ============================================================

output "cognito_user_pool_id" {
  description = "Amazon Cognito user pool ID protecting the Lab 12C API"
  value       = aws_cognito_user_pool.application.id
}

output "cognito_user_pool_client_id" {
  description = "Cognito application client ID used for lab authentication"
  value       = aws_cognito_user_pool_client.application.id
}

output "cognito_authorizer_id" {
  description = "API Gateway Cognito authorizer ID"
  value       = aws_api_gateway_authorizer.cognito.id
}

output "cognito_security_viewers_group" {
  description = "Cognito group for authenticated users without analyze permission"
  value       = aws_cognito_user_group.security_viewers.name
}

output "cognito_security_analysts_group" {
  description = "Cognito group permitted to invoke the protected analysis operation"
  value       = aws_cognito_user_group.security_analysts.name
}

output "cognito_security_admins_group" {
  description = "Cognito administrative group permitted to invoke the protected analysis operation"
  value       = aws_cognito_user_group.security_admins.name
}

output "token_tracking_table_name" {
  description = "DynamoDB table storing token-use telemetry"
  value       = aws_dynamodb_table.token_tracking.name
}

output "unused_token_detector_lambda_name" {
  description = "Lambda function that detects unused token records"
  value       = aws_lambda_function.unused_token_detector.function_name
}

output "unused_token_check_schedule_name" {
  description = "EventBridge Scheduler schedule for unused-token detection"
  value       = aws_scheduler_schedule.unused_token_check.name
}
