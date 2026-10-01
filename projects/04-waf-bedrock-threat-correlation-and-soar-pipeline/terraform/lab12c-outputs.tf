output "compliance_lambda_name" {
  description = "Name of the Lab 12C Compliance Agent Lambda"
  value       = aws_lambda_function.compliance.function_name
}

output "compliance_evidence_table_name" {
  description = "DynamoDB table containing Lab 12C compliance evidence"
  value       = aws_dynamodb_table.compliance_evidence.name
}

output "compliance_report_bucket_name" {
  description = "S3 bucket containing Lab 12C compliance reports"
  value       = aws_s3_bucket.executive_reports.id
}

output "compliance_report_prefix" {
  description = "S3 prefix containing Lab 12C compliance reports"
  value       = var.compliance_report_prefix
}