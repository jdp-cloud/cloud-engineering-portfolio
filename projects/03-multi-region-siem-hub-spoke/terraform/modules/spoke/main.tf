# One spoke region: web tier + local Transit Gateway peered to the hub TGW.
#
# Providers:
#   aws      - the spoke's own region
#   aws.hub  - the hub region (Tokyo); needed to accept the peering and to
#              program the hub TGW route table

terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      configuration_aliases = [aws.hub]
    }
  }
}

module "web" {
  source = "../web-stack"

  providers = { aws = aws }

  name          = var.name
  vpc_cidr      = var.vpc_cidr
  instance_type = var.web_instance_type
  user_data     = var.user_data
}

# --- Local Transit Gateway ----------------------------------------------------
# Default association/propagation are disabled so every route is explicit.
resource "aws_ec2_transit_gateway" "this" {
  description                     = "${var.name} spoke TGW"
  default_route_table_association = "disable"
  default_route_table_propagation = "disable"
  dns_support                     = "enable"

  tags = { Name = "${var.name}-tgw" }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "this" {
  transit_gateway_id = aws_ec2_transit_gateway.this.id
  vpc_id             = module.web.vpc_id
  subnet_ids         = module.web.private_subnet_ids
  dns_support        = "enable"

  tags = { Name = "${var.name}-vpc-attachment" }
}

resource "aws_ec2_transit_gateway_route_table" "this" {
  transit_gateway_id = aws_ec2_transit_gateway.this.id

  tags = { Name = "${var.name}-tgw-rt" }
}

resource "aws_ec2_transit_gateway_route_table_association" "vpc" {
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.this.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.this.id
}

# --- Cross-region peering to the hub -----------------------------------------
resource "aws_ec2_transit_gateway_peering_attachment" "to_hub" {
  transit_gateway_id      = aws_ec2_transit_gateway.this.id
  peer_transit_gateway_id = var.hub_tgw_id
  peer_region             = var.hub_region

  tags = { Name = "${var.name}-to-hub" }
}

resource "aws_ec2_transit_gateway_peering_attachment_accepter" "hub" {
  provider = aws.hub

  transit_gateway_attachment_id = aws_ec2_transit_gateway_peering_attachment.to_hub.id

  tags = { Name = "hub-accepts-${var.name}" }
}

# Route-table associations and routes on a peering attachment only work once the
# hub has accepted it, hence the explicit depends_on below.
resource "aws_ec2_transit_gateway_route_table_association" "peering_spoke_side" {
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_peering_attachment.to_hub.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.this.id

  depends_on = [aws_ec2_transit_gateway_peering_attachment_accepter.hub]
}

resource "aws_ec2_transit_gateway_route_table_association" "peering_hub_side" {
  provider = aws.hub

  transit_gateway_attachment_id  = aws_ec2_transit_gateway_peering_attachment.to_hub.id
  transit_gateway_route_table_id = var.hub_tgw_route_table_id

  depends_on = [aws_ec2_transit_gateway_peering_attachment_accepter.hub]
}

# --- TGW routes ---------------------------------------------------------------
# Spoke TGW: hub networks go over the peering; the spoke's own CIDR goes to its
# VPC (so return traffic arriving from the hub can be delivered).
resource "aws_ec2_transit_gateway_route" "spoke_to_hub" {
  for_each = toset(var.hub_cidrs)

  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.this.id
  destination_cidr_block         = each.value
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_peering_attachment.to_hub.id

  depends_on = [aws_ec2_transit_gateway_route_table_association.peering_spoke_side]
}

resource "aws_ec2_transit_gateway_route" "spoke_local" {
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.this.id
  destination_cidr_block         = var.vpc_cidr
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.this.id
}

# Hub TGW: send this spoke's CIDR back over the peering.
resource "aws_ec2_transit_gateway_route" "hub_to_spoke" {
  provider = aws.hub

  transit_gateway_route_table_id = var.hub_tgw_route_table_id
  destination_cidr_block         = var.vpc_cidr
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_peering_attachment.to_hub.id

  depends_on = [aws_ec2_transit_gateway_route_table_association.peering_hub_side]
}

# --- VPC routes ---------------------------------------------------------------
# Private subnets reach the hub networks through the local TGW.
resource "aws_route" "private_to_hub" {
  for_each = toset(var.hub_cidrs)

  route_table_id         = module.web.private_route_table_id
  destination_cidr_block = each.value
  transit_gateway_id     = aws_ec2_transit_gateway.this.id

  depends_on = [aws_ec2_transit_gateway_vpc_attachment.this]
}
