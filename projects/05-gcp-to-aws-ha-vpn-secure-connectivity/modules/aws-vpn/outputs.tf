# One entry per tunnel, in the order [conn0-tunnel1, conn0-tunnel2,
# conn1-tunnel1, conn1-tunnel2]. The gcp-vpn module consumes this list.
output "tunnels" {
  description = "Outside IP, BGP inside addresses and AWS-side ASN for each of the four tunnels."
  value = flatten([
    for c in aws_vpn_connection.gcp : [
      {
        outside_ip    = c.tunnel1_address
        aws_inside_ip = c.tunnel1_vgw_inside_address
        gcp_inside_ip = c.tunnel1_cgw_inside_address
        aws_asn       = c.tunnel1_bgp_asn
      },
      {
        outside_ip    = c.tunnel2_address
        aws_inside_ip = c.tunnel2_vgw_inside_address
        gcp_inside_ip = c.tunnel2_cgw_inside_address
        aws_asn       = c.tunnel2_bgp_asn
      }
    ]
  ])
}

output "vpn_connection_ids" {
  description = "IDs of the two VPN connections."
  value       = aws_vpn_connection.gcp[*].id
}
