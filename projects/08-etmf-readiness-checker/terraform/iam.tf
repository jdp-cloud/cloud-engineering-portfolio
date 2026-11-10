data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "checker" {
  name               = local.checker_name
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "checker" {
  statement {
    sid     = "ReadIndexAndRules"
    actions = ["s3:GetObject"]
    resources = [
      "${aws_s3_bucket.etmf.arn}/incoming/*",
      "${aws_s3_bucket.etmf.arn}/config/*",
    ]
  }

  statement {
    sid       = "ListIndexAndRules"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.etmf.arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        "incoming/",
        "incoming/*",
        "config/",
        "config/*",
      ]
    }
  }

  statement {
    sid       = "WriteReports"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.etmf.arn}/reports/*"]
  }

  statement {
    sid = "WriteCheckerLogs"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.checker.arn}:*"]
  }
}

resource "aws_iam_role_policy" "checker" {
  name   = "checker"
  role   = aws_iam_role.checker.id
  policy = data.aws_iam_policy_document.checker.json
}

data "aws_iam_policy_document" "scheduler_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler" {
  name               = "p08-etmf-scheduler"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume.json
}

data "aws_iam_policy_document" "scheduler" {
  statement {
    sid       = "InvokeChecker"
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.checker.arn]
  }
}

resource "aws_iam_role_policy" "scheduler" {
  name   = "invoke-checker"
  role   = aws_iam_role.scheduler.id
  policy = data.aws_iam_policy_document.scheduler.json
}
