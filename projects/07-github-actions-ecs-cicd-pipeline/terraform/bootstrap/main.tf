data "aws_caller_identity" "current" {}

locals {
  region      = "us-east-1"
  github_repo = "jdp-cloud/cloud-engineering-portfolio"

  # Environment jobs get sub repo:ORG/REPO:environment:NAME. That sub does
  # not contain the branch, so these policies do not limit deploys to main.
  # GitHub environment branch rules do. Those rules are in docs/github-setup.md.
  staging_sub    = "repo:${local.github_repo}:environment:staging"
  production_sub = "repo:${local.github_repo}:environment:production"

  # The build job has no GitHub environment, so it matches a ref sub.
  ecr_push_sub = "repo:${local.github_repo}:ref:refs/heads/main"

  # Execution role names must match modules/ecs-service-stack. IAM accepts a
  # PassRole ARN for a role that the environment stack creates later.
  staging_execution_role_arn    = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/p07-staging-ecs-execution"
  production_execution_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/p07-production-ecs-execution"

  # Cluster p07-<env>, service and task family p07-<env>-web / p07-<env>-api.
  # Keep this pattern in sync with the module.
  staging_service_arns = [
    "arn:aws:ecs:${local.region}:${data.aws_caller_identity.current.account_id}:service/p07-staging/p07-staging-web",
    "arn:aws:ecs:${local.region}:${data.aws_caller_identity.current.account_id}:service/p07-staging/p07-staging-api",
  ]
  production_service_arns = [
    "arn:aws:ecs:${local.region}:${data.aws_caller_identity.current.account_id}:service/p07-production/p07-production-web",
    "arn:aws:ecs:${local.region}:${data.aws_caller_identity.current.account_id}:service/p07-production/p07-production-api",
  ]

  # Service Authorization Reference for Amazon ECS, fetched 2026-11-02:
  # RegisterTaskDefinition lists resource type task-definition*, so the ARN
  # is the family plus a revision wildcard. DescribeTaskDefinition and
  # ListTaskDefinitions list no resource type.
  staging_task_definition_arns = [
    "arn:aws:ecs:${local.region}:${data.aws_caller_identity.current.account_id}:task-definition/p07-staging-web:*",
    "arn:aws:ecs:${local.region}:${data.aws_caller_identity.current.account_id}:task-definition/p07-staging-api:*",
  ]
  production_task_definition_arns = [
    "arn:aws:ecs:${local.region}:${data.aws_caller_identity.current.account_id}:task-definition/p07-production-web:*",
    "arn:aws:ecs:${local.region}:${data.aws_caller_identity.current.account_id}:task-definition/p07-production-api:*",
  ]
}
