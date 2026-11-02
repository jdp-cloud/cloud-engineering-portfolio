# Shared and pre-existing. The provider for token.actions.githubusercontent.com
# is already in this AWS account. Nothing in this repo creates, imports, or
# manages it. terraform destroy on bootstrap only removes resources in state,
# and this data source is not one of them, so destroy cannot delete it.
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  lifecycle {
    precondition {
      condition     = var.create_github_oidc_provider == false
      error_message = "Refusing to manage the shared GitHub OIDC provider. Leave create_github_oidc_provider false."
    }
  }
}
