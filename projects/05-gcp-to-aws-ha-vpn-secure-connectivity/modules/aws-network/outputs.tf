output "vpc_id" {
  description = "ID of the AWS VPC."
  value       = aws_vpc.this.id
}

output "vpc_cidr" {
  description = "CIDR of the AWS VPC."
  value       = aws_vpc.this.cidr_block
}

output "transit_gateway_id" {
  description = "ID of the Transit Gateway the VPN connections attach to."
  value       = aws_ec2_transit_gateway.this.id
}

output "transit_gateway_asn" {
  description = "Amazon-side BGP ASN of the Transit Gateway."
  value       = aws_ec2_transit_gateway.this.amazon_side_asn
}

output "test_instance_id" {
  description = "ID of the test instance (null when disabled)."
  value       = one(aws_instance.test[*].id)
}

output "test_instance_private_ip" {
  description = "Private IP of the test instance (null when disabled)."
  value       = one(aws_instance.test[*].private_ip)
}
