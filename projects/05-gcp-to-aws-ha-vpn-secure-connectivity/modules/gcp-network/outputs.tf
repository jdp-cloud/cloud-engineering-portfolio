output "network_name" {
  description = "Name of the VPC network."
  value       = google_compute_network.this.name
}

output "subnet_cidr" {
  description = "CIDR of the workload subnet."
  value       = google_compute_subnetwork.this.ip_cidr_range
}

output "ha_vpn_gateway_id" {
  description = "ID of the HA VPN gateway."
  value       = google_compute_ha_vpn_gateway.this.id
}

# Index 0 and 1 map to HA VPN interfaces 0 and 1. Built by matching on the
# interface id so the order never depends on the provider's list order.
output "ha_vpn_gateway_ips" {
  description = "External IPs of HA VPN interface 0 and 1, in that order."
  value = [
    for id in [0, 1] :
    one([for i in google_compute_ha_vpn_gateway.this.vpn_interfaces : i.ip_address if i.id == id])
  ]
}

output "vpn_router_name" {
  description = "Name of the Cloud Router that holds the BGP sessions."
  value       = google_compute_router.vpn.name
}

output "test_vm_name" {
  description = "Name of the test VM (null when disabled)."
  value       = one(google_compute_instance.test[*].name)
}

output "test_vm_private_ip" {
  description = "Private IP of the test VM (null when disabled)."
  value       = one(google_compute_instance.test[*].network_interface[0].network_ip)
}
