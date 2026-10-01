output "gcp_ha_vpn_gateway_ips" {
  description = "External IPs of the two HA VPN interfaces."
  value       = module.gcp_network.ha_vpn_gateway_ips
}

output "aws_tunnels" {
  description = "AWS tunnel outside IPs and BGP inside addresses (no secrets)."
  value       = module.aws_vpn.tunnels
}

output "aws_test_instance_id" {
  description = "Instance ID of the AWS test instance (for SSM)."
  value       = module.aws_network.test_instance_id
}

output "aws_test_instance_private_ip" {
  description = "Private IP of the AWS test instance."
  value       = module.aws_network.test_instance_private_ip
}

output "gcp_test_vm_private_ip" {
  description = "Private IP of the GCP test VM."
  value       = module.gcp_network.test_vm_private_ip
}

# Copy-paste commands for the verification steps. Nothing here contains secrets.
output "verify_commands" {
  description = "Commands to check tunnels, BGP and connectivity after apply."
  value       = <<-EOT
    # 1. GCP tunnels (expect ESTABLISHED on all four)
    gcloud compute vpn-tunnels list --project ${var.gcp_project_id} --format="table(name,region.basename(),status,detailedStatus)"

    # 2. GCP BGP sessions (expect state Established, 4 peers)
    gcloud compute routers get-status ${module.gcp_network.vpn_router_name} --region ${var.gcp_region} --project ${var.gcp_project_id} --format="yaml(result.bgpPeerStatus)"

    # 3. AWS tunnel telemetry (expect Status UP on all four)
    aws ec2 describe-vpn-connections --region ${var.aws_region} --vpn-connection-ids ${join(" ", module.aws_vpn.vpn_connection_ids)} --query "VpnConnections[].VgwTelemetry[].[OutsideIpAddress,Status,StatusMessage]" --output table

    # 4. Shell on the AWS test instance (SSM), then ping / iperf3 the GCP VM
    aws ssm start-session --region ${var.aws_region} --target ${coalesce(module.aws_network.test_instance_id, "n/a")}
    ping -c 4 ${coalesce(module.gcp_network.test_vm_private_ip, "n/a")}
    iperf3 -c ${coalesce(module.gcp_network.test_vm_private_ip, "n/a")} -t 20 -P 4

    # 5. Shell on the GCP test VM (IAP), then ping / iperf3 the AWS instance
    gcloud compute ssh ${coalesce(module.gcp_network.test_vm_name, "n/a")} --zone ${var.gcp_zone} --project ${var.gcp_project_id} --tunnel-through-iap
    ping -c 4 ${coalesce(module.aws_network.test_instance_private_ip, "n/a")}
    iperf3 -c ${coalesce(module.aws_network.test_instance_private_ip, "n/a")} -t 20 -P 4
  EOT
}
