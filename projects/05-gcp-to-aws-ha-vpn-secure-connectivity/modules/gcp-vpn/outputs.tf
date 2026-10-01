output "tunnel_names" {
  description = "Names of the four Cloud VPN tunnels."
  value       = google_compute_vpn_tunnel.aws[*].name
}

output "bgp_peer_names" {
  description = "Names of the four BGP peers on the Cloud Router."
  value       = google_compute_router_peer.aws[*].name
}
