variable "environment" {
  description = "staging or production. Used in resource names and the /p07/<environment>/ SSM prefix."
  type        = string

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be staging or production."
  }
}

variable "region" {
  description = "AWS region. The environment root pins the provider to the same region."
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "IPv4 CIDR for this environment VPC. Staging and production use different blocks."
  type        = string

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "vpc_cidr must be a valid IPv4 CIDR block."
  }
}

variable "public_subnets" {
  description = "Exactly two public subnets. Availability zones are chosen by the caller so this module does not use an AZ data source."
  type = map(object({
    cidr = string
    az   = string
  }))

  validation {
    condition     = length(var.public_subnets) == 2
    error_message = "Provide exactly two public subnets."
  }

  validation {
    condition = alltrue([
      for subnet in values(var.public_subnets) : contains(["us-east-1a", "us-east-1b"], subnet.az)
    ])
    error_message = "Subnets must use us-east-1a or us-east-1b."
  }
}

variable "allowed_ingress_cidrs" {
  description = "IPv4 CIDRs allowed to open the public HTTP listener. The lab default is the internet."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "api_image" {
  description = "API image pinned by digest, as repository-url@sha256:<64 hex>. No default. Push an image before the first apply."
  type        = string

  validation {
    condition     = can(regex("^[^\\s]+@sha256:[0-9a-f]{64}$", var.api_image))
    error_message = "api_image must be a repository URI followed by @sha256: and 64 hex characters."
  }
}

variable "web_image" {
  description = "Web image pinned by digest, as repository-url@sha256:<64 hex>. No default. Push an image before the first apply."
  type        = string

  validation {
    condition     = can(regex("^[^\\s]+@sha256:[0-9a-f]{64}$", var.web_image))
    error_message = "web_image must be a repository URI followed by @sha256: and 64 hex characters."
  }
}
