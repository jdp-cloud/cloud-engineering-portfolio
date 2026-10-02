variable "name_prefix" {
  description = "Prefix for resource names."
  type        = string
}

variable "transit_gateway_id" {
  description = "Transit Gateway that the VPN connections attach to."
  type        = string
}

variable "gcp_gateway_ips" {
  description = "External IPs of HA VPN interface 0 and 1 (one customer gateway each)."
  type        = list(string)

  validation {
    condition     = length(var.gcp_gateway_ips) == 2
    error_message = "Exactly two GCP HA VPN interface IPs are required."
  }
}

variable "gcp_bgp_asn" {
  description = "BGP ASN of the GCP Cloud Router."
  type        = number
}

variable "tunnel_inside_cidrs" {
  description = "Four /30 link-local ranges (169.254.0.0/16), one per tunnel, in tunnel order."
  type        = list(string)

  validation {
    condition     = length(var.tunnel_inside_cidrs) == 4
    error_message = "Exactly four inside CIDRs are required (two per VPN connection)."
  }
}

variable "preshared_keys" {
  description = "Four pre-shared keys, one per tunnel, in tunnel order."
  type        = list(string)
  sensitive   = true

  validation {
    condition     = length(var.preshared_keys) == 4
    error_message = "Exactly four pre-shared keys are required."
  }
}

variable "crypto" {
  description = <<-EOT
    IPsec/IKE algorithms, identical on all four tunnels. Google recommends a
    single AEAD cipher. phase2_integrity is omitted for AEAD ciphers, which
    carry their own integrity. To fall back to CBC use phase1_encryption and
    phase2_encryption = "AES256" with phase2_integrity = "SHA2-256".
  EOT
  type = object({
    phase1_encryption = string
    phase1_integrity  = string
    phase2_encryption = string
    phase2_integrity  = optional(string)
    dh_group          = number
  })
  default = {
    phase1_encryption = "AES256-GCM-16"
    phase1_integrity  = "SHA2-256"
    phase2_encryption = "AES256-GCM-16"
    phase2_integrity  = null
    dh_group          = 20
  }
}
