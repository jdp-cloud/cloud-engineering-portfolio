resource "aws_cloudwatch_log_group" "classifier" {
  count = var.enable_bedrock ? 1 : 0

  name              = "/aws/lambda/${local.classifier_name}"
  retention_in_days = 14
}

resource "aws_iam_role" "classifier" {
  count = var.enable_bedrock ? 1 : 0

  name               = local.classifier_name
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "classifier" {
  count = var.enable_bedrock ? 1 : 0

  statement {
    sid       = "ReadSyntheticPdf"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.etmf.arn}/incoming/pdf/*"]
  }

  statement {
    sid       = "WriteClassificationOnly"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.etmf.arn}/reports/classifications/*"]
  }

  statement {
    sid       = "InvokeOneModel"
    actions   = ["bedrock:InvokeModel"]
    resources = ["arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_model_id}"]
  }

  statement {
    sid = "WriteClassifierLogs"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.classifier[0].arn}:*"]
  }
}

resource "aws_iam_role_policy" "classifier" {
  count = var.enable_bedrock ? 1 : 0

  name   = "classifier"
  role   = aws_iam_role.classifier[0].id
  policy = data.aws_iam_policy_document.classifier[0].json
}

resource "aws_lambda_function" "classifier" {
  count = var.enable_bedrock ? 1 : 0

  function_name    = local.classifier_name
  role             = aws_iam_role.classifier[0].arn
  runtime          = "python3.12"
  architectures    = ["arm64"]
  handler          = "classifier.handler.lambda_handler"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  memory_size      = 512
  timeout          = 60

  environment {
    variables = {
      BEDROCK_MODEL_ID = var.bedrock_model_id
    }
  }

  depends_on = [
    aws_iam_role_policy.classifier,
    aws_cloudwatch_log_group.classifier,
  ]
}

resource "aws_lambda_permission" "classifier" {
  count = var.enable_bedrock ? 1 : 0

  statement_id  = "AllowS3InvokeClassifier"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.classifier[0].function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.etmf.arn
}
