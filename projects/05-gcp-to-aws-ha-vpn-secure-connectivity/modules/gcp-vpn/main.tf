# GCP side of the HA VPN: the peer (AWS) gateway with four interfaces, four
# IKEv2 tunnels, and a BGP interface + peer on the Cloud Router per tunnel.
#
# Tunnel n uses HA VPN interface floor(n / 2) and AWS peer interface n, which
# matches how the aws-vpn module lays out connection 0 (tunnels 0-1) and
# connection 1 (tunnels 2-3).

resource "google_compute_external_vpn_gateway" "aws" {
  name            = "${var.name_prefix}-aws-peer-gw"
  description     = "AWS Site-to-Site VPN tunnel endpoints"
  redundancy_type = "FOUR_IPS_REDUNDANCY"

  dynamic "interface" {
    for_each = var.tunnels
    content {
      id         = interface.key
      ip_address = interface.value.outside_ip
    }
  }
}

resource "google_compute_vpn_tunnel" "aws" {
  count = length(var.tunnels)

  name                            = "${var.name_prefix}-tunnel-${count.index}"
  region                          = var.region
  vpn_gateway                     = var.ha_vpn_gateway_id
  vpn_gateway_interface           = floor(count.index / 2)
  peer_external_gateway           = google_compute_external_vpn_gateway.aws.id
  peer_external_gateway_interface = count.index
  shared_secret                   = var.preshared_keys[count.index]
  router                          = var.router_name
  ike_version                     = 2
}

resource "google_compute_router_interface" "aws" {
  count = length(var.tunnels)

  name       = "${var.name_prefix}-if-${count.index}"
  region     = var.region
  router     = var.router_name
  ip_range   = "${var.tunnels[count.index].gcp_inside_ip}/30"
  vpn_tunnel = google_compute_vpn_tunnel.aws[count.index].name
}

resource "google_compute_router_peer" "aws" {
  count = length(var.tunnels)

  name                      = "${var.name_prefix}-peer-${count.index}"
  region                    = var.region
  router                    = var.router_name
  interface                 = google_compute_router_interface.aws[count.index].name
  peer_ip_address           = var.tunnels[count.index].aws_inside_ip
  peer_asn                  = tonumber(var.tunnels[count.index].aws_asn)
  advertised_route_priority = var.advertised_route_priority
}
