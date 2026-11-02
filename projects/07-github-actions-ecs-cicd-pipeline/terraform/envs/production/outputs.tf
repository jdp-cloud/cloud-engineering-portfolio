output "alb_dns_name" {
  description = "Public DNS name of the production load balancer."
  value       = module.stack.alb_dns_name
}

output "cluster_name" {
  description = "Production ECS cluster name."
  value       = module.stack.cluster_name
}

output "web_service_name" {
  description = "Production web service name."
  value       = module.stack.web_service_name
}

output "api_service_name" {
  description = "Production API service name."
  value       = module.stack.api_service_name
}

output "execution_role_arn" {
  description = "Production task execution role ARN."
  value       = module.stack.execution_role_arn
}

output "vpc_id" {
  description = "Production VPC ID."
  value       = module.stack.vpc_id
}
