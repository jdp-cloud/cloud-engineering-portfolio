variable "name" {
  description = "Short name for the spoke, e.g. \"london\"."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the spoke VPC."
  type        = string
}

variable "user_data" {
  description = "Plain-text user-data script for the web instances."
  type        = string
}

variable "web_instance_type" {
  type    = string
  default = "t3.micro"
}

variable "hub_region" {
  description = "Region name of the hub Transit Gateway (needed for cross-region peering)."
  type        = string
}

variable "hub_tgw_id" {
  description = "ID of the hub Transit Gateway to peer with."
  type        = string
}

variable "hub_tgw_route_table_id" {
  description = "Hub TGW route table that this spoke's peering attachment is associated with."
  type        = string
}

variable "hub_cidrs" {
  description = "Hub-side CIDRs this spoke must be able to reach (Tokyo web VPC and the security zone)."
  type        = list(string)
}
