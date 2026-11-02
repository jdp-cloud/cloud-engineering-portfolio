variable "create_github_oidc_provider" {
  description = "Must stay false. The GitHub OIDC provider for token.actions.githubusercontent.com already exists in this account and is shared. This stack only looks it up. It does not create, import, or manage the provider, so terraform destroy cannot delete it."
  type        = bool
  default     = false

  validation {
    condition     = var.create_github_oidc_provider == false
    error_message = "Leave create_github_oidc_provider false. This project must not create or manage the shared GitHub OIDC provider."
  }
}

variable "budget_alert_email" {
  description = "Address that receives the $10 monthly budget alert. Set it in terraform.tfvars (gitignored). Do not commit a real address."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.budget_alert_email))
    error_message = "budget_alert_email must look like an email address."
  }
}
