output "siem_instance_id" {
  description = "Instance ID of the Loki/Grafana server (use with SSM Session Manager)."
  value       = aws_instance.siem.id
}

output "grafana_port_forward_command" {
  description = "Run this locally, then open http://localhost:3000"
  value       = "aws ssm start-session --region ap-northeast-1 --target ${aws_instance.siem.id} --document-name AWS-StartPortForwardingSession --parameters portNumber=3000,localPortNumber=3000"
}

output "web_endpoints" {
  description = "Public ALB DNS name for each web tier."
  value = {
    tokyo      = module.web_tokyo.alb_dns_name
    london     = module.spoke_london.alb_dns_name
    new_york   = module.spoke_new_york.alb_dns_name
    sao_paulo  = module.spoke_sao_paulo.alb_dns_name
    sydney     = module.spoke_sydney.alb_dns_name
    california = module.spoke_california.alb_dns_name
    hong_kong  = module.spoke_hong_kong.alb_dns_name
  }
}
