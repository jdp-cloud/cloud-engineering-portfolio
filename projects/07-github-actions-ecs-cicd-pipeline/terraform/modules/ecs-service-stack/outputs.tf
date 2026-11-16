output "alb_dns_name" {
  description = "Public DNS name of the application load balancer."
  value       = aws_lb.this.dns_name
}

output "cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.this.name
}

output "web_service_name" {
  description = "ECS service name for the web app."
  value       = aws_ecs_service.web.name
}

output "api_service_name" {
  description = "ECS service name for the API."
  value       = aws_ecs_service.api.name
}

output "execution_role_arn" {
  description = "Task execution role ARN. Bootstrap grants iam:PassRole on this name."
  value       = aws_iam_role.execution.arn
}

output "vpc_id" {
  description = "VPC ID for this environment."
  value       = aws_vpc.this.id
}
