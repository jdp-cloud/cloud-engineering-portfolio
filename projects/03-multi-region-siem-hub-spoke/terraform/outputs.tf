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

# --- Proof outputs ------------------------------------------------------------------------
# These are computed from the real resources above, so they change if the design
# changes. They exist so a reviewer can see the isolation rules without reading
# every security group.

output "isolation_proof" {
  description = "Facts about log and database isolation, computed from the deployed configuration."
  value = {
    data_residency = {
      log_store_region   = local.hub_region
      database_region    = local.hub_region
      database_engine    = aws_rds_cluster.pii.engine
      cross_region_links = "Transit Gateway peering over the AWS backbone; no VPN in this design"
    }

    subnet_layout = {
      siem_subnet      = { cidr = aws_subnet.security_private.cidr_block, az = aws_subnet.security_private.availability_zone }
      database_subnets = [for s in [aws_subnet.security_db_a, aws_subnet.security_db_b] : { cidr = s.cidr_block, az = s.availability_zone }]
      public_subnets   = [{ cidr = aws_subnet.security_public.cidr_block, az = aws_subnet.security_public.availability_zone, purpose = "NAT gateway only" }]
    }

    checks = {
      siem_az_has_public_subnet     = contains(local.public_subnet_azs, aws_subnet.security_private.availability_zone)
      database_az_has_public_subnet = length(setintersection(local.db_az_names, local.public_subnet_azs)) > 0
      siem_and_database_share_subnet = (
        aws_subnet.security_private.id == aws_subnet.security_db_a.id ||
        aws_subnet.security_private.id == aws_subnet.security_db_b.id
      )
      siem_allows_ssh_or_grafana_inbound = length([for r in aws_vpc_security_group_ingress_rule.siem_loki : r if r.from_port != 3100]) > 0
      any_spoke_cidr_allowed_to_database = length([for c in values(local.spoke_cidrs) : c if contains(local.db_allowed_cidrs, c)]) > 0
    }
  }
}

output "siem_inbound_rules" {
  description = "Every inbound rule on the SIEM security group. Only Loki push (TCP 3100) from the web VPCs."
  value = {
    for k, r in aws_vpc_security_group_ingress_rule.siem_loki :
    k => "tcp/${r.from_port} from ${r.cidr_ipv4}"
  }
}

output "database_inbound_rules" {
  description = "Every inbound rule on the database security group. Only the Tokyo web VPC."
  value = {
    for k, r in aws_vpc_security_group_ingress_rule.db_mysql :
    k => "tcp/${r.from_port} from ${r.cidr_ipv4}"
  }
}

output "database_master_secret_arn" {
  description = "Secrets Manager secret holding the generated database password (the value is not printed)."
  value       = aws_rds_cluster.pii.master_user_secret[0].secret_arn
}
