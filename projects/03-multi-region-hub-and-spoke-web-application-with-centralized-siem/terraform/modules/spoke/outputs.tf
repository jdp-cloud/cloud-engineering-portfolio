output "vpc_cidr" {
  value = module.web.vpc_cidr
}

output "alb_dns_name" {
  value = module.web.alb_dns_name
}

output "tgw_id" {
  value = aws_ec2_transit_gateway.this.id
}
