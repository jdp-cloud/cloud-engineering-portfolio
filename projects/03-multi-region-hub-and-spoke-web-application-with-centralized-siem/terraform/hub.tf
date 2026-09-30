# Hub region (Tokyo, ap-northeast-1):
#   * Hub Transit Gateway + one route table shared by every attachment
#   * Tokyo web VPC (same web-stack module as the spokes)
#   * Security zone VPC hosting the Loki/Grafana SIEM server and the Aurora database

data "aws_availability_zones" "tokyo" {
  provider = aws.tokyo
  state    = "available"
}

data "aws_ssm_parameter" "al2023_tokyo" {
  provider = aws.tokyo
  name     = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# --- Hub Transit Gateway --------------------------------------------------------
resource "aws_ec2_transit_gateway" "hub" {
  provider = aws.tokyo

  description                     = "Hub TGW (Tokyo)"
  default_route_table_association = "disable"
  default_route_table_propagation = "disable"
  dns_support                     = "enable"

  tags = { Name = "hub-tgw-tokyo" }
}

resource "aws_ec2_transit_gateway_route_table" "hub" {
  provider = aws.tokyo

  transit_gateway_id = aws_ec2_transit_gateway.hub.id

  tags = { Name = "hub-tgw-rt" }
}

# --- Tokyo web VPC ----------------------------------------------------------------
module "web_tokyo" {
  source = "./modules/web-stack"

  providers = { aws = aws.tokyo }

  name          = "tokyo"
  vpc_cidr      = local.hub_web_cidr
  instance_type = var.web_instance_type
  user_data     = local.web_user_data

  instance_profile_name = aws_iam_instance_profile.web.name
}

resource "aws_ec2_transit_gateway_vpc_attachment" "tokyo_web" {
  provider = aws.tokyo

  transit_gateway_id = aws_ec2_transit_gateway.hub.id
  vpc_id             = module.web_tokyo.vpc_id
  subnet_ids         = module.web_tokyo.private_subnet_ids
  dns_support        = "enable"

  tags = { Name = "tokyo-web-attachment" }
}

resource "aws_ec2_transit_gateway_route_table_association" "tokyo_web" {
  provider = aws.tokyo

  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.tokyo_web.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.hub.id
}

resource "aws_ec2_transit_gateway_route" "hub_to_tokyo_web" {
  provider = aws.tokyo

  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.hub.id
  destination_cidr_block         = local.hub_web_cidr
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.tokyo_web.id
}

# Tokyo web instances also ship logs to Loki, which lives in the security zone.
resource "aws_route" "tokyo_web_to_security" {
  provider = aws.tokyo

  route_table_id         = module.web_tokyo.private_route_table_id
  destination_cidr_block = local.security_cidr
  transit_gateway_id     = aws_ec2_transit_gateway.hub.id

  depends_on = [aws_ec2_transit_gateway_vpc_attachment.tokyo_web]
}

# --- Security zone VPC --------------------------------------------------------------
resource "aws_vpc" "security" {
  provider = aws.tokyo

  cidr_block           = local.security_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "security-zone-vpc" }
}

resource "aws_default_security_group" "security" {
  provider = aws.tokyo

  vpc_id = aws_vpc.security.id

  tags = { Name = "security-default-sg-unused" }
}

# Layout of the security zone across three Availability Zones:
#
#   AZ[0]  private subnet: SIEM server        private subnet: Aurora (a)
#   AZ[1]  private subnet: Aurora (b)
#   AZ[2]  public subnet:  NAT gateway only
#
# The AZs that hold log data and the database have no public subnet at all.
# The SIEM and the database also live in different subnets.
resource "aws_subnet" "security_private" {
  provider = aws.tokyo

  vpc_id            = aws_vpc.security.id
  cidr_block        = cidrsubnet(local.security_cidr, 8, 0)
  availability_zone = data.aws_availability_zones.tokyo.names[0]

  tags = { Name = "security-siem-private", Service = "log-collection" }
}

resource "aws_subnet" "security_db_a" {
  provider = aws.tokyo

  vpc_id            = aws_vpc.security.id
  cidr_block        = cidrsubnet(local.security_cidr, 8, 2)
  availability_zone = data.aws_availability_zones.tokyo.names[0]

  tags = { Name = "security-db-private-a", Service = "pii-database" }
}

resource "aws_subnet" "security_db_b" {
  provider = aws.tokyo

  vpc_id            = aws_vpc.security.id
  cidr_block        = cidrsubnet(local.security_cidr, 8, 3)
  availability_zone = data.aws_availability_zones.tokyo.names[1]

  tags = { Name = "security-db-private-b", Service = "pii-database" }
}

# The only public subnet in this VPC. It sits in its own AZ and hosts nothing but
# the NAT gateway that gives the SIEM outbound HTTPS for package installs.
resource "aws_subnet" "security_public" {
  provider = aws.tokyo

  vpc_id            = aws_vpc.security.id
  cidr_block        = cidrsubnet(local.security_cidr, 8, 1)
  availability_zone = data.aws_availability_zones.tokyo.names[2]

  tags = { Name = "security-public-nat-only" }
}

resource "aws_internet_gateway" "security" {
  provider = aws.tokyo

  vpc_id = aws_vpc.security.id

  tags = { Name = "security-igw" }
}

resource "aws_eip" "security_nat" {
  provider = aws.tokyo

  domain = "vpc"

  tags = { Name = "security-nat-eip" }
}

resource "aws_nat_gateway" "security" {
  provider = aws.tokyo

  allocation_id = aws_eip.security_nat.id
  subnet_id     = aws_subnet.security_public.id

  tags = { Name = "security-nat" }

  depends_on = [aws_internet_gateway.security]
}

resource "aws_route_table" "security_public" {
  provider = aws.tokyo

  vpc_id = aws_vpc.security.id

  tags = { Name = "security-public-rt" }
}

resource "aws_route" "security_public_internet" {
  provider = aws.tokyo

  route_table_id         = aws_route_table.security_public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.security.id
}

resource "aws_route_table_association" "security_public" {
  provider = aws.tokyo

  subnet_id      = aws_subnet.security_public.id
  route_table_id = aws_route_table.security_public.id
}

resource "aws_route_table" "security_private" {
  provider = aws.tokyo

  vpc_id = aws_vpc.security.id

  tags = { Name = "security-private-rt" }
}

resource "aws_route" "security_private_nat" {
  provider = aws.tokyo

  route_table_id         = aws_route_table.security_private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.security.id
}

# Return path: SIEM replies to every web VPC via the hub TGW.
resource "aws_route" "security_to_web_vpcs" {
  provider = aws.tokyo
  for_each = merge(local.spoke_cidrs, { tokyo = local.hub_web_cidr })

  route_table_id         = aws_route_table.security_private.id
  destination_cidr_block = each.value
  transit_gateway_id     = aws_ec2_transit_gateway.hub.id

  depends_on = [aws_ec2_transit_gateway_vpc_attachment.security]
}

resource "aws_route_table_association" "security_private" {
  provider = aws.tokyo

  subnet_id      = aws_subnet.security_private.id
  route_table_id = aws_route_table.security_private.id
}

# Database subnets get their own route table with NO internet route. The only
# routes are the local VPC and the return path to the Tokyo web VPC.
resource "aws_route_table" "security_db" {
  provider = aws.tokyo

  vpc_id = aws_vpc.security.id

  tags = { Name = "security-db-rt-isolated" }
}

resource "aws_route" "security_db_to_tokyo_web" {
  provider = aws.tokyo

  route_table_id         = aws_route_table.security_db.id
  destination_cidr_block = local.hub_web_cidr
  transit_gateway_id     = aws_ec2_transit_gateway.hub.id

  depends_on = [aws_ec2_transit_gateway_vpc_attachment.security]
}

resource "aws_route_table_association" "security_db_a" {
  provider = aws.tokyo

  subnet_id      = aws_subnet.security_db_a.id
  route_table_id = aws_route_table.security_db.id
}

resource "aws_route_table_association" "security_db_b" {
  provider = aws.tokyo

  subnet_id      = aws_subnet.security_db_b.id
  route_table_id = aws_route_table.security_db.id
}

resource "aws_ec2_transit_gateway_vpc_attachment" "security" {
  provider = aws.tokyo

  transit_gateway_id = aws_ec2_transit_gateway.hub.id
  vpc_id             = aws_vpc.security.id
  # One subnet per AZ that hosts workloads: the SIEM/DB-a AZ and the DB-b AZ.
  subnet_ids  = [aws_subnet.security_private.id, aws_subnet.security_db_b.id]
  dns_support = "enable"

  tags = { Name = "security-zone-attachment" }
}

resource "aws_ec2_transit_gateway_route_table_association" "security" {
  provider = aws.tokyo

  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.security.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.hub.id
}

resource "aws_ec2_transit_gateway_route" "hub_to_security" {
  provider = aws.tokyo

  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.hub.id
  destination_cidr_block         = local.security_cidr
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.security.id
}

# --- SIEM server -----------------------------------------------------------------------
resource "aws_security_group" "siem" {
  provider = aws.tokyo

  name        = "siem-sg"
  description = "Loki ingest from web VPCs only; no SSH, no inbound Grafana"
  vpc_id      = aws_vpc.security.id

  tags = { Name = "siem-sg" }
}

# Only the seven web VPCs may push logs. Grafana (3000) is bound to localhost and
# reached through SSM, and there is no SSH rule at all.
resource "aws_vpc_security_group_ingress_rule" "siem_loki" {
  provider = aws.tokyo
  for_each = merge(local.spoke_cidrs, { tokyo = local.hub_web_cidr })

  security_group_id = aws_security_group.siem.id
  description       = "Loki push from ${each.key} web VPC"
  ip_protocol       = "tcp"
  from_port         = 3100
  to_port           = 3100
  cidr_ipv4         = each.value
}

resource "aws_vpc_security_group_egress_rule" "siem_https" {
  provider = aws.tokyo

  security_group_id = aws_security_group.siem.id
  description       = "HTTPS for package installs and the SSM agent"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_iam_role" "siem" {
  provider = aws.tokyo

  name = "${var.project_name}-siem-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

# Session Manager access via the AWS-managed least-privilege policy for SSM.
resource "aws_iam_role_policy_attachment" "siem_ssm" {
  provider = aws.tokyo

  role       = aws_iam_role.siem.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "siem" {
  provider = aws.tokyo

  name = "${var.project_name}-siem-profile"
  role = aws_iam_role.siem.name
}

resource "aws_instance" "siem" {
  provider = aws.tokyo

  ami                         = data.aws_ssm_parameter.al2023_tokyo.value
  instance_type               = var.siem_instance_type
  subnet_id                   = aws_subnet.security_private.id
  private_ip                  = local.siem_private_ip
  vpc_security_group_ids      = [aws_security_group.siem.id]
  iam_instance_profile        = aws_iam_instance_profile.siem.name
  associate_public_ip_address = false

  user_data = templatefile("${path.module}/scripts/siem-loki-grafana.sh.tftpl", {
    loki_version       = local.loki_version
    loki_sha256        = local.loki_sha256
    loki_internal_port = local.loki_internal_port
  })
  user_data_replace_on_change = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  tags = { Name = "siem-server" }

  # Guard rail: the AZ holding log data must never contain a public subnet.
  lifecycle {
    precondition {
      condition     = !contains(local.public_subnet_azs, aws_subnet.security_private.availability_zone)
      error_message = "The SIEM server's Availability Zone contains a public subnet. Log data must stay in private-only AZs."
    }
    precondition {
      condition     = aws_subnet.security_private.id != aws_subnet.security_db_a.id && aws_subnet.security_private.id != aws_subnet.security_db_b.id
      error_message = "The SIEM server and the database must not share a subnet."
    }
  }

  # The instance downloads packages at first boot, so NAT must be ready.
  depends_on = [aws_route.security_private_nat, aws_route_table_association.security_private]
}

# --- SIEM fault tolerance ----------------------------------------------------------------
# If the underlying host fails, EC2 restarts the instance on healthy hardware. The
# instance keeps its ID, its private IP (10.77.0.10) and its EBS volume, so Loki's
# stored logs survive and Promtail agents reconnect on their own.
resource "aws_cloudwatch_metric_alarm" "siem_auto_recover" {
  provider = aws.tokyo

  alarm_name          = "${var.project_name}-siem-auto-recover"
  alarm_description   = "Recover the SIEM server if the EC2 system status check fails"
  namespace           = "AWS/EC2"
  metric_name         = "StatusCheckFailed_System"
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "missing"

  dimensions    = { InstanceId = aws_instance.siem.id }
  alarm_actions = ["arn:aws:automate:${local.hub_region}:ec2:recover"]
}

# --- PII database (Tokyo only) --------------------------------------------------------------
# The only database in the design, and it exists only in Tokyo. Its subnets are in
# AZs with no public subnet, in a route table with no internet route, and only the
# Tokyo web VPC may connect. Spoke regions have no permitted path to it.
resource "aws_db_subnet_group" "pii" {
  provider = aws.tokyo

  name       = "${var.project_name}-pii"
  subnet_ids = [aws_subnet.security_db_a.id, aws_subnet.security_db_b.id]

  tags = { Name = "pii-db-subnet-group" }
}

resource "aws_security_group" "db" {
  provider = aws.tokyo

  name        = "pii-db-sg"
  description = "Aurora MySQL: reachable only from the Tokyo web VPC"
  vpc_id      = aws_vpc.security.id

  tags = { Name = "pii-db-sg" }
}

resource "aws_vpc_security_group_ingress_rule" "db_mysql" {
  provider = aws.tokyo
  for_each = toset(local.db_allowed_cidrs)

  security_group_id = aws_security_group.db.id
  description       = "MySQL from the Tokyo web VPC"
  ip_protocol       = "tcp"
  from_port         = 3306
  to_port           = 3306
  cidr_ipv4         = each.value
}

resource "aws_rds_cluster" "pii" {
  provider = aws.tokyo

  cluster_identifier = "${var.project_name}-pii"
  engine             = "aurora-mysql"
  database_name      = "appdata"
  master_username    = "dbadmin"

  # AWS generates the password and keeps it in Secrets Manager: it never appears
  # in the code, the plan output or (in plaintext) the Terraform state.
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.pii.name
  vpc_security_group_ids = [aws_security_group.db.id]
  storage_encrypted      = true

  iam_database_authentication_enabled = true
  backup_retention_period             = 1
  copy_tags_to_snapshot               = true

  # Lab settings so `terraform destroy` finishes cleanly. Production would keep
  # deletion protection on and take a final snapshot.
  deletion_protection = false
  skip_final_snapshot = true

  lifecycle {
    precondition {
      condition     = length(setintersection(local.db_az_names, local.public_subnet_azs)) == 0
      error_message = "A database subnet is in an Availability Zone that contains a public subnet."
    }
  }
}

resource "aws_rds_cluster_instance" "pii_writer" {
  provider = aws.tokyo

  identifier           = "${var.project_name}-pii-writer"
  cluster_identifier   = aws_rds_cluster.pii.id
  engine               = aws_rds_cluster.pii.engine
  instance_class       = "db.t3.medium"
  db_subnet_group_name = aws_db_subnet_group.pii.name
  publicly_accessible  = false
}

# --- Web tier access: SSM instead of SSH ---------------------------------------------------
# The web instances get the same Session Manager role as the SIEM, so operators can
# open a shell to run tests (for example, confirming a spoke cannot query Loki).
resource "aws_iam_role" "web" {
  provider = aws.tokyo

  name = "${var.project_name}-web-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "web_ssm" {
  provider = aws.tokyo

  role       = aws_iam_role.web.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "web" {
  provider = aws.tokyo

  name = "${var.project_name}-web-profile"
  role = aws_iam_role.web.name
}
