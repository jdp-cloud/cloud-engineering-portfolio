variable "enable_compliance_bedrock" {
  description = "Enable Bedrock-generated compliance narrative; deterministic reporting remains available when disabled"
  type        = bool
  default     = false
}

variable "compliance_report_prefix" {
  description = "S3 key prefix for Lab 12c compliance PDF and JSON reports"
  type        = string
  default     = "compliance-reports"

  validation {
    condition = (
      length(trimspace(var.compliance_report_prefix)) > 0 &&
      !startswith(var.compliance_report_prefix, "/") &&
      !endswith(var.compliance_report_prefix, "/")
    )

    error_message = "compliance_report_prefix must not begin or end with a slash."
  }
}

variable "compliance_report_title" {
  description = "Title displayed in Lab 12c compliance reports"
  type        = string
  default     = "Compliance Evidence Report"
}
