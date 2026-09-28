# Six spoke regions, one module call each. Terraform cannot loop over provider
# aliases, so the calls are explicit; everything else lives in modules/spoke.

module "spoke_london" {
  source    = "./modules/spoke"
  providers = { aws = aws.london, aws.hub = aws.tokyo }

  name                   = "london"
  vpc_cidr               = local.spoke_cidrs.london
  user_data              = local.web_user_data
  web_instance_type      = var.web_instance_type
  hub_region             = local.hub_region
  hub_tgw_id             = aws_ec2_transit_gateway.hub.id
  hub_tgw_route_table_id = aws_ec2_transit_gateway_route_table.hub.id
  hub_cidrs              = local.hub_cidrs
}

module "spoke_new_york" {
  source    = "./modules/spoke"
  providers = { aws = aws.new_york, aws.hub = aws.tokyo }

  name                   = "new-york"
  vpc_cidr               = local.spoke_cidrs.new_york
  user_data              = local.web_user_data
  web_instance_type      = var.web_instance_type
  hub_region             = local.hub_region
  hub_tgw_id             = aws_ec2_transit_gateway.hub.id
  hub_tgw_route_table_id = aws_ec2_transit_gateway_route_table.hub.id
  hub_cidrs              = local.hub_cidrs
}

module "spoke_sao_paulo" {
  source    = "./modules/spoke"
  providers = { aws = aws.sao_paulo, aws.hub = aws.tokyo }

  name                   = "sao-paulo"
  vpc_cidr               = local.spoke_cidrs.sao_paulo
  user_data              = local.web_user_data
  web_instance_type      = var.web_instance_type
  hub_region             = local.hub_region
  hub_tgw_id             = aws_ec2_transit_gateway.hub.id
  hub_tgw_route_table_id = aws_ec2_transit_gateway_route_table.hub.id
  hub_cidrs              = local.hub_cidrs
}

module "spoke_sydney" {
  source    = "./modules/spoke"
  providers = { aws = aws.sydney, aws.hub = aws.tokyo }

  name                   = "sydney"
  vpc_cidr               = local.spoke_cidrs.sydney
  user_data              = local.web_user_data
  web_instance_type      = var.web_instance_type
  hub_region             = local.hub_region
  hub_tgw_id             = aws_ec2_transit_gateway.hub.id
  hub_tgw_route_table_id = aws_ec2_transit_gateway_route_table.hub.id
  hub_cidrs              = local.hub_cidrs
}

module "spoke_california" {
  source    = "./modules/spoke"
  providers = { aws = aws.california, aws.hub = aws.tokyo }

  name                   = "california"
  vpc_cidr               = local.spoke_cidrs.california
  user_data              = local.web_user_data
  web_instance_type      = var.web_instance_type
  hub_region             = local.hub_region
  hub_tgw_id             = aws_ec2_transit_gateway.hub.id
  hub_tgw_route_table_id = aws_ec2_transit_gateway_route_table.hub.id
  hub_cidrs              = local.hub_cidrs
}

module "spoke_hong_kong" {
  source    = "./modules/spoke"
  providers = { aws = aws.hong_kong, aws.hub = aws.tokyo }

  name                   = "hong-kong"
  vpc_cidr               = local.spoke_cidrs.hong_kong
  user_data              = local.web_user_data
  web_instance_type      = var.web_instance_type
  hub_region             = local.hub_region
  hub_tgw_id             = aws_ec2_transit_gateway.hub.id
  hub_tgw_route_table_id = aws_ec2_transit_gateway_route_table.hub.id
  hub_cidrs              = local.hub_cidrs
}
