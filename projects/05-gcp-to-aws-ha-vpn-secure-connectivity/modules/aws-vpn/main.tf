# AWS side of the HA VPN: one customer gateway per GCP HA VPN interface and
# one VPN connection per customer gateway (two tunnels each = four tunnels),
# attached to the Transit Gateway and routed with BGP.

locals {
  phase2_integrity = var.crypto.phase2_integrity == null ? null : [var.crypto.phase2_integrity]
}

resource "aws_customer_gateway" "gcp" {
  count = 2

  bgp_asn    = var.gcp_bgp_asn
  ip_address = var.gcp_gateway_ips[count.index]
  type       = "ipsec.1"

  tags = {
    Name = "${var.name_prefix}-cgw-${count.index}"
  }
}

resource "aws_vpn_connection" "gcp" {
  count = 2

  transit_gateway_id  = var.transit_gateway_id
  customer_gateway_id = aws_customer_gateway.gcp[count.index].id
  type                = "ipsec.1"
  static_routes_only  = false

  # Tunnel 1 of this connection
  tunnel1_inside_cidr    = var.tunnel_inside_cidrs[count.index * 2]
  tunnel1_preshared_key  = var.preshared_keys[count.index * 2]
  tunnel1_startup_action = "start"

  tunnel1_ike_versions                 = ["ikev2"]
  tunnel1_phase1_encryption_algorithms = [var.crypto.phase1_encryption]
  tunnel1_phase1_integrity_algorithms  = [var.crypto.phase1_integrity]
  tunnel1_phase1_dh_group_numbers      = [var.crypto.dh_group]
  tunnel1_phase2_encryption_algorithms = [var.crypto.phase2_encryption]
  tunnel1_phase2_integrity_algorithms  = local.phase2_integrity
  tunnel1_phase2_dh_group_numbers      = [var.crypto.dh_group]

  # Tunnel 2 of this connection
  tunnel2_inside_cidr    = var.tunnel_inside_cidrs[count.index * 2 + 1]
  tunnel2_preshared_key  = var.preshared_keys[count.index * 2 + 1]
  tunnel2_startup_action = "start"

  tunnel2_ike_versions                 = ["ikev2"]
  tunnel2_phase1_encryption_algorithms = [var.crypto.phase1_encryption]
  tunnel2_phase1_integrity_algorithms  = [var.crypto.phase1_integrity]
  tunnel2_phase1_dh_group_numbers      = [var.crypto.dh_group]
  tunnel2_phase2_encryption_algorithms = [var.crypto.phase2_encryption]
  tunnel2_phase2_integrity_algorithms  = local.phase2_integrity
  tunnel2_phase2_dh_group_numbers      = [var.crypto.dh_group]

  tags = {
    Name = "${var.name_prefix}-vpn-${count.index}"
  }
}
