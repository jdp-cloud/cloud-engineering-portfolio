variable "gcp_project_id" {
  description = "GCP project ID to deploy into (no default on purpose)."
  type        = string
}

variable "gcp_region" {
  description = "GCP region. us-east4 (N. Virginia) pairs with AWS us-east-1 for the phase 2 Interconnect."
  type        = string
  default     = "us-east4"
}

variable "gcp_zone" {
  description = "GCP zone for the test VM."
  type        = string
  default     = "us-east4-a"
}

variable "aws_region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "Optional AWS CLI/SSO profile name. Null uses the default credential chain."
  type        = string
  default     = null
}

variable "name_prefix" {
  description = "Prefix for resource names on both clouds."
  type        = string
  default     = "gcp-aws-vpn"
}

variable "aws_vpc_cidr" {
  description = "CIDR of the AWS VPC. Must not overlap with the GCP subnet."
  type        = string
  default     = "10.230.0.0/16"
}

variable "gcp_subnet_cidr" {
  description = "CIDR of the GCP subnet. Must not overlap with the AWS VPC."
  type        = string
  default     = "10.240.0.0/24"
}

variable "gcp_router_asn" {
  description = "Private BGP ASN for the GCP Cloud Router."
  type        = number
  default     = 65515
}

variable "aws_tgw_asn" {
  description = "Amazon-side BGP ASN for the Transit Gateway."
  type        = number
  default     = 65501
}

# AWS reserves several ranges in 169.254.0.0/16 (for example 169.254.0.0/30 to
# 169.254.5.0/30 and 169.254.169.252/30). These four are outside them.
variable "tunnel_inside_cidrs" {
  description = "Four /30 link-local ranges for the BGP sessions, one per tunnel."
  type        = list(string)
  default = [
    "169.254.0.8/30",
    "169.254.0.12/30",
    "169.254.0.16/30",
    "169.254.0.20/30",
  ]
}

variable "enable_test_workloads" {
  description = "Create a private test VM on each side (used for ping and iperf3)."
  type        = bool
  default     = true
}
