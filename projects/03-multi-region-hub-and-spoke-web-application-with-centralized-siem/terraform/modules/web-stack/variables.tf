variable "name" {
  description = "Short name for the location, e.g. \"london\". Used in resource names."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC (a /16)."
  type        = string
}

variable "az_count" {
  description = "Number of Availability Zones to spread across (the ALB needs at least 2)."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2
    error_message = "An Application Load Balancer needs subnets in at least two Availability Zones."
  }
}

variable "instance_type" {
  description = "EC2 instance type for the web tier."
  type        = string
  default     = "t3.micro"
}

variable "user_data" {
  description = "Plain-text user-data script for the web instances (encoded by the module)."
  type        = string
}

variable "asg_min_size" {
  type    = number
  default = 2
}

variable "asg_max_size" {
  type    = number
  default = 3
}

variable "asg_desired_capacity" {
  type    = number
  default = 2
}

variable "instance_profile_name" {
  description = "IAM instance profile for the web instances (Session Manager access; there is no SSH)."
  type        = string
}
