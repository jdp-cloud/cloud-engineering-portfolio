resource "aws_lambda_function" "application" {
  function_name = local.function_names.application
  description   = "Returns a test response for the protected API endpoint"

  role    = aws_iam_role.application.arn
  handler = "protected_api_handler.lambda_handler"
  runtime = "python3.12"

  filename         = data.archive_file.application.output_path
  source_code_hash = data.archive_file.application.output_base64sha256

  memory_size = 128
  timeout     = 10

  environment {
    variables = {
      TOKEN_TABLE_NAME = aws_dynamodb_table.token_tracking.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.application,
    aws_iam_role_policy.application,
  ]
}
