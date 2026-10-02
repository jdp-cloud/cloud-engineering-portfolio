variable "name_prefix" {
  description = "Prefix for resource names."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR of the AWS VPC."
  type        = string
}

variable "remote_cidr" {
  description = "CIDR of the GCP subnet. Only this range is allowed to reach the test instance."
  type        = string
}

variable "tgw_asn" {
  description = "Amazon-side BGP ASN of the Transit Gateway (64512-65534)."
  type        = number
}

variable "enable_test_instance" {
  description = "Create the private test instance and the SSM endpoints it needs."
  type        = bool
  default     = true
}

variable "instance_type" {
  description = "Instance type for the test instance."
  type        = string
  default     = "t3.micro"
}

variable "flow_log_retention_days" {
  description = "Retention for VPC flow logs in CloudWatch Logs (security logs: keep at least a year)."
  type        = number
  default     = 365
}
