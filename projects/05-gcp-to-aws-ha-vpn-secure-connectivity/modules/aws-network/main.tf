# AWS side of the network: a private VPC (no internet gateway, no NAT), a
# Transit Gateway with ECMP enabled for the VPN, and an optional private test
# instance managed through SSM over VPC endpoints.

data "aws_availability_zones" "available" {
  # checkov:skip=CKV_AWS_394: only the first AZ name is used, so a newly added AZ cannot change the result
  state = "available"
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

locals {
  az                = data.aws_availability_zones.available.names[0]
  flow_log_group    = "/aws/vpc/${var.name_prefix}/flow-logs"
  ssm_endpoint_list = ["ssm", "ssmmessages", "ec2messages"]
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.name_prefix}-vpc"
  }
}

# Lock the default security group down to nothing so nothing can use it by accident.
resource "aws_default_security_group" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-default-locked"
  }
}

resource "aws_subnet" "workload" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 0)
  availability_zone       = local.az
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.name_prefix}-workload"
  }
}

resource "aws_route_table" "workload" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-workload"
  }
}

resource "aws_route_table_association" "workload" {
  subnet_id      = aws_subnet.workload.id
  route_table_id = aws_route_table.workload.id
}

# ---------------------------------------------------------------------------
# Transit Gateway. vpn_ecmp_support lets traffic use all four tunnels.
# ---------------------------------------------------------------------------
resource "aws_ec2_transit_gateway" "this" {
  description                     = "${var.name_prefix} hub for the GCP HA VPN"
  amazon_side_asn                 = var.tgw_asn
  auto_accept_shared_attachments  = "disable"
  default_route_table_association = "enable"
  default_route_table_propagation = "enable"
  dns_support                     = "enable"
  vpn_ecmp_support                = "enable"

  tags = {
    Name = "${var.name_prefix}-tgw"
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "this" {
  transit_gateway_id = aws_ec2_transit_gateway.this.id
  vpc_id             = aws_vpc.this.id
  subnet_ids         = [aws_subnet.workload.id]

  tags = {
    Name = "${var.name_prefix}-vpc-attachment"
  }
}

# Send traffic for the GCP range to the Transit Gateway.
resource "aws_route" "to_gcp" {
  route_table_id         = aws_route_table.workload.id
  destination_cidr_block = var.remote_cidr
  transit_gateway_id     = aws_ec2_transit_gateway.this.id

  depends_on = [aws_ec2_transit_gateway_vpc_attachment.this]
}

# ---------------------------------------------------------------------------
# VPC flow logs to CloudWatch Logs, encrypted with a customer-managed key.
# ---------------------------------------------------------------------------
resource "aws_kms_key" "logs" {
  description             = "${var.name_prefix} flow log encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 7

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AccountAdmin"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowCloudWatchLogs"
        Effect    = "Allow"
        Principal = { Service = "logs.${data.aws_region.current.region}.amazonaws.com" }
        Action = [
          "kms:Encrypt*",
          "kms:Decrypt*",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:Describe*"
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:log-group:${local.flow_log_group}"
          }
        }
      }
    ]
  })
}

resource "aws_kms_alias" "logs" {
  name          = "alias/${var.name_prefix}-flow-logs"
  target_key_id = aws_kms_key.logs.key_id
}

resource "aws_cloudwatch_log_group" "flow" {
  name              = local.flow_log_group
  retention_in_days = var.flow_log_retention_days
  kms_key_id        = aws_kms_key.logs.arn
}

data "aws_iam_policy_document" "flow_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["vpc-flow-logs.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

data "aws_iam_policy_document" "flow_write" {
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.flow.arn}:*"]
  }
}

resource "aws_iam_role" "flow" {
  name               = "${var.name_prefix}-flow-logs"
  assume_role_policy = data.aws_iam_policy_document.flow_assume.json
}

resource "aws_iam_role_policy" "flow" {
  name   = "write-flow-logs"
  role   = aws_iam_role.flow.id
  policy = data.aws_iam_policy_document.flow_write.json
}

resource "aws_flow_log" "vpc" {
  vpc_id               = aws_vpc.this.id
  traffic_type         = "ALL"
  log_destination_type = "cloud-watch-logs"
  log_destination      = aws_cloudwatch_log_group.flow.arn
  iam_role_arn         = aws_iam_role.flow.arn

  tags = {
    Name = "${var.name_prefix}-vpc-flow-log"
  }
}

# ---------------------------------------------------------------------------
# Private test instance, managed with SSM (no SSH, no public IP, no inbound
# from the internet). SSM and the AL2023 package repos are reached through
# VPC endpoints, so the VPC needs no internet gateway or NAT.
# ---------------------------------------------------------------------------
resource "aws_security_group" "endpoints" {
  # checkov:skip=CKV2_AWS_5: attached to the SSM interface endpoints through for_each, which the check cannot follow
  count = var.enable_test_instance ? 1 : 0

  name        = "${var.name_prefix}-endpoints"
  description = "HTTPS from the VPC to the SSM interface endpoints"
  vpc_id      = aws_vpc.this.id
}

resource "aws_vpc_security_group_ingress_rule" "endpoints_https" {
  count = var.enable_test_instance ? 1 : 0

  security_group_id = aws_security_group.endpoints[0].id
  description       = "HTTPS from the VPC"
  cidr_ipv4         = var.vpc_cidr
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_endpoint" "ssm" {
  for_each = var.enable_test_instance ? toset(local.ssm_endpoint_list) : toset([])

  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${data.aws_region.current.region}.${each.key}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.workload.id]
  security_group_ids  = [aws_security_group.endpoints[0].id]
  private_dns_enabled = true

  tags = {
    Name = "${var.name_prefix}-${each.key}"
  }
}

# The Amazon Linux 2023 package repositories are served from S3.
resource "aws_vpc_endpoint" "s3" {
  count = var.enable_test_instance ? 1 : 0

  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${data.aws_region.current.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.workload.id]

  tags = {
    Name = "${var.name_prefix}-s3"
  }
}

resource "aws_security_group" "test" {
  name        = "${var.name_prefix}-test"
  description = "Test instance: ICMP and iperf3 from the GCP range only"
  vpc_id      = aws_vpc.this.id
}

resource "aws_vpc_security_group_ingress_rule" "icmp_from_gcp" {
  security_group_id = aws_security_group.test.id
  description       = "ICMP from GCP"
  cidr_ipv4         = var.remote_cidr
  ip_protocol       = "icmp"
  from_port         = -1
  to_port           = -1
}

resource "aws_vpc_security_group_ingress_rule" "iperf_tcp_from_gcp" {
  security_group_id = aws_security_group.test.id
  description       = "iperf3 (TCP) from GCP"
  cidr_ipv4         = var.remote_cidr
  ip_protocol       = "tcp"
  from_port         = 5201
  to_port           = 5201
}

resource "aws_vpc_security_group_ingress_rule" "iperf_udp_from_gcp" {
  security_group_id = aws_security_group.test.id
  description       = "iperf3 (UDP) from GCP"
  cidr_ipv4         = var.remote_cidr
  ip_protocol       = "udp"
  from_port         = 5201
  to_port           = 5201
}

# Egress stays inside the VPC: SSM endpoints (443) and the S3 gateway endpoint.
resource "aws_vpc_security_group_egress_rule" "https_to_vpc" {
  security_group_id = aws_security_group.test.id
  description       = "HTTPS to the SSM endpoints"
  cidr_ipv4         = var.vpc_cidr
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

data "aws_prefix_list" "s3" {
  name = "com.amazonaws.${data.aws_region.current.region}.s3"
}

resource "aws_vpc_security_group_egress_rule" "https_to_s3" {
  security_group_id = aws_security_group.test.id
  description       = "HTTPS to S3 (package repositories)"
  prefix_list_id    = data.aws_prefix_list.s3.id
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_security_group_egress_rule" "replies_to_gcp" {
  security_group_id = aws_security_group.test.id
  description       = "Replies and iperf3 traffic back to GCP"
  cidr_ipv4         = var.remote_cidr
  ip_protocol       = "-1"
}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ssm" {
  count = var.enable_test_instance ? 1 : 0

  name               = "${var.name_prefix}-test-ssm"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

resource "aws_iam_role_policy_attachment" "ssm" {
  count = var.enable_test_instance ? 1 : 0

  role       = aws_iam_role.ssm[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ssm" {
  count = var.enable_test_instance ? 1 : 0

  name = "${var.name_prefix}-test-ssm"
  role = aws_iam_role.ssm[0].name
}

data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_instance" "test" {
  count = var.enable_test_instance ? 1 : 0

  ami                         = data.aws_ssm_parameter.al2023.insecure_value
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.workload.id
  vpc_security_group_ids      = [aws_security_group.test.id]
  iam_instance_profile        = aws_iam_instance_profile.ssm[0].name
  associate_public_ip_address = false
  monitoring                  = true
  ebs_optimized               = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2 only
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted   = true
    volume_type = "gp3"
  }

  user_data = <<-EOT
    #!/bin/bash
    set -euo pipefail
    dnf install -y iperf3
    cat >/etc/systemd/system/iperf3.service <<'UNIT'
    [Unit]
    Description=iperf3 server
    After=network-online.target

    [Service]
    ExecStart=/usr/bin/iperf3 -s
    Restart=always

    [Install]
    WantedBy=multi-user.target
    UNIT
    systemctl daemon-reload
    systemctl enable --now iperf3
  EOT

  user_data_replace_on_change = true

  tags = {
    Name = "${var.name_prefix}-test"
  }

  depends_on = [
    aws_vpc_endpoint.ssm,
    aws_vpc_endpoint.s3,
  ]
}
