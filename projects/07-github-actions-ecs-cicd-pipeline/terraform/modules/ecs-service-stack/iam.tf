# Name must stay p07-<environment>-ecs-execution. Bootstrap grants PassRole
# on that ARN before this role exists.

data "aws_iam_policy_document" "ecs_tasks_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "execution" {
  statement {
    sid     = "AuthToken"
    effect  = "Allow"
    actions = ["ecr:GetAuthorizationToken"]
    # Service Authorization Reference for Amazon ECR: GetAuthorizationToken
    # has no resource type, so IAM requires "*".
    resources = ["*"]
  }

  statement {
    sid    = "PullImages"
    effect = "Allow"
    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
    resources = [
      data.aws_ecr_repository.web.arn,
      data.aws_ecr_repository.api.arn,
    ]
  }

  statement {
    sid    = "WriteLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "${aws_cloudwatch_log_group.web.arn}:*",
      "${aws_cloudwatch_log_group.api.arn}:*",
    ]
  }

  statement {
    sid       = "ReadParameters"
    effect    = "Allow"
    actions   = ["ssm:GetParameters"]
    resources = ["arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/p07/${var.environment}/*"]
  }

  # No kms:Decrypt. EXAMPLE_SECRET is a SecureString on the AWS-managed
  # aws/ssm key, not a customer-managed key. Add kms:Decrypt on that key
  # only if a customer-managed key is introduced.
}

resource "aws_iam_role" "execution" {
  name               = "p07-${var.environment}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_trust.json
}

resource "aws_iam_role_policy" "execution" {
  name   = "p07-${var.environment}-ecs-execution"
  role   = aws_iam_role.execution.id
  policy = data.aws_iam_policy_document.execution.json
}
