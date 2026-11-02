data "aws_iam_policy_document" "gha_staging_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.staging_sub]
    }
  }
}

data "aws_iam_policy_document" "gha_production_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.production_sub]
    }
  }
}

data "aws_iam_policy_document" "gha_ecr_push_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.ecr_push_sub]
    }
  }
}

data "aws_iam_policy_document" "staging_deploy" {
  statement {
    sid    = "UpdateAndDescribeServices"
    effect = "Allow"
    actions = [
      "ecs:UpdateService",
      "ecs:DescribeServices",
    ]
    resources = local.staging_service_arns
  }

  statement {
    sid       = "RegisterTaskDefinition"
    effect    = "Allow"
    actions   = ["ecs:RegisterTaskDefinition"]
    resources = local.staging_task_definition_arns
  }

  statement {
    sid    = "ReadTaskDefinitions"
    effect = "Allow"
    actions = [
      "ecs:DescribeTaskDefinition",
      "ecs:ListTaskDefinitions",
    ]
    # Service Authorization Reference for Amazon ECS, fetched 2026-11-02:
    # these two actions have no resource type, so IAM requires "*".
    resources = ["*"]
  }

  statement {
    sid       = "PassExecutionRole"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = [local.staging_execution_role_arn]

    # There is no task role. The containers do not call AWS APIs, so PassRole
    # covers only the execution role. Add the task role ARN here if that changes.
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "production_deploy" {
  statement {
    sid    = "UpdateAndDescribeServices"
    effect = "Allow"
    actions = [
      "ecs:UpdateService",
      "ecs:DescribeServices",
    ]
    resources = local.production_service_arns
  }

  statement {
    sid       = "RegisterTaskDefinition"
    effect    = "Allow"
    actions   = ["ecs:RegisterTaskDefinition"]
    resources = local.production_task_definition_arns
  }

  statement {
    sid    = "ReadTaskDefinitions"
    effect = "Allow"
    actions = [
      "ecs:DescribeTaskDefinition",
      "ecs:ListTaskDefinitions",
    ]
    # Service Authorization Reference for Amazon ECS, fetched 2026-11-02:
    # these two actions have no resource type, so IAM requires "*".
    resources = ["*"]
  }

  statement {
    sid       = "PassExecutionRole"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = [local.production_execution_role_arn]

    # There is no task role. PassRole covers only the execution role.
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "ecr_push" {
  statement {
    sid     = "AuthToken"
    effect  = "Allow"
    actions = ["ecr:GetAuthorizationToken"]
    # Service Authorization Reference for Amazon ECR: GetAuthorizationToken
    # has no resource type, so IAM requires "*".
    resources = ["*"]
  }

  statement {
    sid    = "PushAndPull"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:CompleteLayerUpload",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
    resources = [
      aws_ecr_repository.web.arn,
      aws_ecr_repository.api.arn,
    ]
  }
}

resource "aws_iam_role" "staging_deploy" {
  name               = "p07-gha-staging-deploy"
  assume_role_policy = data.aws_iam_policy_document.gha_staging_trust.json

  tags = {
    Environment = "staging"
  }
}

resource "aws_iam_role_policy" "staging_deploy" {
  name   = "p07-gha-staging-deploy"
  role   = aws_iam_role.staging_deploy.id
  policy = data.aws_iam_policy_document.staging_deploy.json
}

resource "aws_iam_role" "production_deploy" {
  name               = "p07-gha-production-deploy"
  assume_role_policy = data.aws_iam_policy_document.gha_production_trust.json

  tags = {
    Environment = "production"
  }
}

resource "aws_iam_role_policy" "production_deploy" {
  name   = "p07-gha-production-deploy"
  role   = aws_iam_role.production_deploy.id
  policy = data.aws_iam_policy_document.production_deploy.json
}

resource "aws_iam_role" "ecr_push" {
  name               = "p07-gha-ecr-push"
  assume_role_policy = data.aws_iam_policy_document.gha_ecr_push_trust.json
}

resource "aws_iam_role_policy" "ecr_push" {
  name   = "p07-gha-ecr-push"
  role   = aws_iam_role.ecr_push.id
  policy = data.aws_iam_policy_document.ecr_push.json
}
