data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/../build/checker.zip"
  excludes    = ["**/__pycache__/**", "**/*.pyc"]
}

resource "aws_lambda_function" "checker" {
  function_name    = local.checker_name
  role             = aws_iam_role.checker.arn
  runtime          = "python3.12"
  architectures    = ["arm64"]
  handler          = "checker.handler.lambda_handler"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  memory_size      = 256
  timeout          = 30

  environment {
    variables = {
      BUCKET_NAME    = aws_s3_bucket.etmf.id
      RULES_KEY      = aws_s3_object.rules.key
      MILESTONES_KEY = aws_s3_object.milestones.key
    }
  }

  depends_on = [
    aws_iam_role_policy.checker,
    aws_cloudwatch_log_group.checker,
  ]
}

resource "aws_lambda_permission" "s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.checker.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.etmf.arn
}

resource "aws_s3_bucket_notification" "incoming" {
  bucket = aws_s3_bucket.etmf.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.checker.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "incoming/"
    filter_suffix       = ".csv"
  }

  dynamic "lambda_function" {
    for_each = var.enable_bedrock ? [1] : []
    content {
      lambda_function_arn = aws_lambda_function.classifier[0].arn
      events              = ["s3:ObjectCreated:*"]
      filter_prefix       = "incoming/pdf/"
      filter_suffix       = ".pdf"
    }
  }

  depends_on = [
    aws_lambda_permission.s3,
    aws_lambda_permission.classifier,
  ]
}
