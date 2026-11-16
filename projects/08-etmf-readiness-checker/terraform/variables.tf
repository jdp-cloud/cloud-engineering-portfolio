variable "aws_region" {
  type        = string
  description = "AWS region for every resource in this demo."
  default     = "us-east-1"
}

variable "budget_alert_email" {
  type        = string
  description = "Address that receives the monthly $5 budget alarm. Set it in terraform.tfvars, which is gitignored."
  sensitive   = true

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.budget_alert_email))
    error_message = "budget_alert_email must look like an email address."
  }
}

variable "force_destroy" {
  type        = bool
  description = "Allow terraform destroy to delete versioned objects in the lab buckets. Leave true for this demo."
  default     = true
}

variable "upload_sample_index" {
  type        = bool
  description = "Upload the committed synthetic index so the weekly check has an object to read."
  default     = true
}

variable "enable_bedrock" {
  type        = bool
  description = "Create the optional PDF classifier Lambda. Leave false unless Bedrock model access is already enabled."
  default     = false
}

variable "bedrock_model_id" {
  type        = string
  description = "Bedrock model id used only when enable_bedrock is true. Use a Claude model the account is allowed to invoke."
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "enable_cloudtrail_data_events" {
  type        = bool
  description = "Record S3 object-level events for the eTMF bucket. Off by default because data events are the cost driver."
  default     = false
}
