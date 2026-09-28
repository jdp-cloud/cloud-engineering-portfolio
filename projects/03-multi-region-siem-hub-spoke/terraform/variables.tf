variable "project_name" {
  description = "Prefix used for resource names and the Project tag."
  type        = string
  default     = "siem-hub-spoke"
}

variable "web_instance_type" {
  description = "Instance type for the web tier in every region."
  type        = string
  default     = "t3.micro"
}

variable "siem_instance_type" {
  description = "Instance type for the Loki/Grafana SIEM server."
  type        = string
  default     = "t3.medium"
}
