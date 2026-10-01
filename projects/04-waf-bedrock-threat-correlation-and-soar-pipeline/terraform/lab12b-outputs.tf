output "executive_dashboard_lambda_name" {
  description = "Name of the Lab 12B executive-dashboard Lambda function"
  value       = aws_lambda_function.executive_dashboard.function_name
}

output "executive_report_bucket_name" {
  description = "Name of the private S3 bucket containing executive PDF and JSON reports"
  value       = aws_s3_bucket.executive_reports.id
}

output "executive_report_prefix" {
  description = "S3 key prefix containing executive-report artifacts"
  value       = var.report_prefix
}

output "reportlab_layer_arn" {
  description = "ARN of the ReportLab Python 3.12 x86_64 Lambda layer"
  value       = aws_lambda_layer_version.reportlab.arn
}
