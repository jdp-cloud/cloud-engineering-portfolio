variable "name_prefix" {
  description = "Prefix for resource names."
  type        = string
}

variable "region" {
  description = "GCP region of the HA VPN gateway and Cloud Router."
  type        = string
}

variable "ha_vpn_gateway_id" {
  description = "ID of the HA VPN gateway."
  type        = string
}

variable "router_name" {
  description = "Name of the Cloud Router that holds the BGP sessions."
  type        = string
}

variable "tunnels" {
  description = "The four AWS tunnels, in order, as produced by the aws-vpn module."
  type = list(object({
    outside_ip    = string
    aws_inside_ip = string
    gcp_inside_ip = string
    aws_asn       = string
  }))

  validation {
    condition     = length(var.tunnels) == 4
    error_message = "Exactly four tunnels are required."
  }
}

variable "preshared_keys" {
  description = "Four pre-shared keys, one per tunnel, matching the AWS side."
  type        = list(string)
  sensitive   = true

  validation {
    condition     = length(var.preshared_keys) == 4
    error_message = "Exactly four pre-shared keys are required."
  }
}

variable "advertised_route_priority" {
  description = "BGP MED that Cloud Router advertises on all four sessions."
  type        = number
  default     = 100
}
