variable "api_image" {
  description = "API image pinned by digest (repository-url@sha256:<64 hex>). No default. Set it in terraform.tfvars after the first push."
  type        = string

  validation {
    condition     = can(regex("^[^\\s]+@sha256:[0-9a-f]{64}$", var.api_image))
    error_message = "api_image must be a repository URI followed by @sha256: and 64 hex characters."
  }
}

variable "web_image" {
  description = "Web image pinned by digest (repository-url@sha256:<64 hex>). No default. Set it in terraform.tfvars after the first push."
  type        = string

  validation {
    condition     = can(regex("^[^\\s]+@sha256:[0-9a-f]{64}$", var.web_image))
    error_message = "web_image must be a repository URI followed by @sha256: and 64 hex characters."
  }
}

variable "allowed_ingress_cidrs" {
  description = "IPv4 CIDRs allowed to open the public HTTP listener."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
