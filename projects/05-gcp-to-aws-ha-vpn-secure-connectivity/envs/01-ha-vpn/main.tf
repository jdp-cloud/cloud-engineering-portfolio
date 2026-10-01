# Phase 1: HA VPN between Google Cloud and AWS.
#
# Order of dependencies (there is no cycle, but the data flows both ways):
#   1. gcp_network  creates the HA VPN gateway -> its two external IPs
#   2. aws_network  creates the VPC and Transit Gateway
#   3. aws_vpn      uses the GCP IPs to create customer gateways + VPN connections
#                   -> AWS tunnel outside IPs, inside IPs and ASN
#   4. gcp_vpn      uses the AWS tunnel details to build the peer gateway,
#                   tunnels and BGP sessions

resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "iap.googleapis.com",
  ])

  project            = var.gcp_project_id
  service            = each.value
  disable_on_destroy = false
}

# Pre-shared keys are generated here, never typed into the repo. They live only
# in the (encrypted, private) remote state. AWS requires 8-64 characters from
# [A-Za-z0-9._] and forbids a leading zero, hence the fixed "k" prefix.
resource "random_password" "psk" {
  count = 4

  length  = 32
  special = false
}

locals {
  preshared_keys = [for p in random_password.psk : "k${p.result}"]
}

module "gcp_network" {
  source = "../../modules/gcp-network"

  name_prefix    = var.name_prefix
  region         = var.gcp_region
  zone           = var.gcp_zone
  subnet_cidr    = var.gcp_subnet_cidr
  remote_cidr    = var.aws_vpc_cidr
  router_asn     = var.gcp_router_asn
  enable_test_vm = var.enable_test_workloads

  depends_on = [google_project_service.apis]
}

module "aws_network" {
  source = "../../modules/aws-network"

  name_prefix          = var.name_prefix
  vpc_cidr             = var.aws_vpc_cidr
  remote_cidr          = var.gcp_subnet_cidr
  tgw_asn              = var.aws_tgw_asn
  enable_test_instance = var.enable_test_workloads
}

module "aws_vpn" {
  source = "../../modules/aws-vpn"

  name_prefix         = var.name_prefix
  transit_gateway_id  = module.aws_network.transit_gateway_id
  gcp_gateway_ips     = module.gcp_network.ha_vpn_gateway_ips
  gcp_bgp_asn         = var.gcp_router_asn
  tunnel_inside_cidrs = var.tunnel_inside_cidrs
  preshared_keys      = local.preshared_keys
}

module "gcp_vpn" {
  source = "../../modules/gcp-vpn"

  name_prefix       = var.name_prefix
  region            = var.gcp_region
  ha_vpn_gateway_id = module.gcp_network.ha_vpn_gateway_id
  router_name       = module.gcp_network.vpn_router_name
  tunnels           = module.aws_vpn.tunnels
  preshared_keys    = local.preshared_keys
}
