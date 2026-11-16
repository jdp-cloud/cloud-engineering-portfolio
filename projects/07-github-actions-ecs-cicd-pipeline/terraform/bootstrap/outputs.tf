output "ecr_web_repository_url" {
  description = "Registry URL for the p07-web repository. Push the first image here before applying an environment."
  value       = aws_ecr_repository.web.repository_url
}

output "ecr_api_repository_url" {
  description = "Registry URL for the p07-api repository. Push the first image here before applying an environment."
  value       = aws_ecr_repository.api.repository_url
}

output "gha_staging_deploy_role_arn" {
  description = "Role assumed by the staging GitHub environment."
  value       = aws_iam_role.staging_deploy.arn
}

output "gha_production_deploy_role_arn" {
  description = "Role assumed by the production GitHub environment."
  value       = aws_iam_role.production_deploy.arn
}

output "gha_ecr_push_role_arn" {
  description = "Role assumed by the build job on main. That job has no GitHub environment."
  value       = aws_iam_role.ecr_push.arn
}

output "github_oidc_provider_arn" {
  description = "Looked up, not created. The shared GitHub OIDC provider is pre-existing and is not destroyed with this stack."
  value       = data.aws_iam_openid_connect_provider.github.arn
}

output "budget_name" {
  description = "Monthly $10 cost budget for the p07-ecs-cicd tag."
  value       = aws_budgets_budget.p07.name
}
