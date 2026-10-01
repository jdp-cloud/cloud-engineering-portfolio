variable "name_prefix" {
  description = "Prefix for resource names (lowercase letters, digits, hyphens; 3-20 chars)."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,18}[a-z0-9]$", var.name_prefix))
    error_message = "name_prefix must be 3-20 chars: lowercase letters, digits and hyphens, starting with a letter."
  }
}

variable "region" {
  description = "GCP region for the subnet, HA VPN gateway and Cloud Routers."
  type        = string
}

variable "zone" {
  description = "GCP zone for the test VM."
  type        = string
}

variable "subnet_cidr" {
  description = "CIDR range of the workload subnet."
  type        = string
}

variable "remote_cidr" {
  description = "CIDR of the AWS VPC. Only this range is allowed to reach the test VM."
  type        = string
}

variable "router_asn" {
  description = "Private BGP ASN for the VPN Cloud Router (64512-65534)."
  type        = number
}

variable "enable_test_vm" {
  description = "Create the private test VM, its Cloud NAT and firewall rules."
  type        = bool
  default     = true
}

variable "enable_flow_logs" {
  description = "Enable VPC flow logs on the workload subnet."
  type        = bool
  default     = true
}
