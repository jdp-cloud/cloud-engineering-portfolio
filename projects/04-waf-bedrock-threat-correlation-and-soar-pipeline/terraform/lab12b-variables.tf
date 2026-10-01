variable "enable_executive_bedrock" {
  description = "Enable Bedrock-generated executive narrative text; deterministic reporting remains available when disabled"
  type        = bool
  default     = true
}

variable "max_items_per_table" {
  description = "Maximum number of records read from each DynamoDB table for one executive report"
  type        = number
  default     = 5000

  validation {
    condition = (
      var.max_items_per_table >= 1 &&
      var.max_items_per_table <= 10000
    )
    error_message = "max_items_per_table must be between 1 and 10000."
  }
}

variable "organization_name" {
  description = "Organization name displayed in executive reports"
  type        = string
  default     = "SEIR Cloud Security"

  validation {
    condition     = length(trimspace(var.organization_name)) > 0
    error_message = "organization_name must not be empty."
  }
}

variable "report_bucket_force_destroy" {
  description = "Allow Terraform destroy to remove report objects and versions from the lab S3 bucket"
  type        = bool
  default     = true
}

variable "report_period_hours" {
  description = "Default current and comparison reporting-window duration in hours"
  type        = number
  default     = 24

  validation {
    condition = (
      var.report_period_hours >= 1 &&
      var.report_period_hours <= 720
    )
    error_message = "report_period_hours must be between 1 and 720."
  }
}

variable "report_prefix" {
  description = "S3 key prefix under which executive PDF and JSON reports are stored"
  type        = string
  default     = "executive-reports"

  validation {
    condition = (
      length(trimspace(var.report_prefix)) > 0 &&
      !startswith(var.report_prefix, "/") &&
      !endswith(var.report_prefix, "/")
    )
    error_message = "report_prefix must be non-empty and must not begin or end with a slash."
  }
}

variable "report_title" {
  description = "Title displayed in executive reports"
  type        = string
  default     = "Executive Security Report"

  validation {
    condition     = length(trimspace(var.report_title)) > 0
    error_message = "report_title must not be empty."
  }
}
