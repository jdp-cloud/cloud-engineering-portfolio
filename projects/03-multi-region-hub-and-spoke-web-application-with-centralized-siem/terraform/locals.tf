# Central address plan. Every VPC gets a /16 out of 10.70.0.0/12 so nothing overlaps.
#
#   10.70.0.0/16  Tokyo web VPC (hub region)
#   10.71.0.0/16  London          10.74.0.0/16  Sydney
#   10.72.0.0/16  New York        10.75.0.0/16  California
#   10.73.0.0/16  Sao Paulo       10.76.0.0/16  Hong Kong
#   10.77.0.0/16  Security zone (SIEM) in Tokyo

locals {
  hub_web_cidr  = "10.70.0.0/16"
  security_cidr = "10.77.0.0/16"

  spoke_cidrs = {
    london     = "10.71.0.0/16"
    new_york   = "10.72.0.0/16"
    sao_paulo  = "10.73.0.0/16"
    sydney     = "10.74.0.0/16"
    california = "10.75.0.0/16"
    hong_kong  = "10.76.0.0/16"
  }

  hub_region = "ap-northeast-1"
  hub_cidrs  = [local.hub_web_cidr, local.security_cidr]

  # Loki listens on localhost only; an nginx gateway on :3100 exposes the push path.
  loki_internal_port = 3101

  # Only the Tokyo web VPC may reach the database. No spoke CIDR is listed here.
  db_allowed_cidrs = [local.hub_web_cidr]

  # Availability Zones that contain a public subnet / database subnets, used by the
  # guard-rail preconditions in hub.tf.
  public_subnet_azs = [aws_subnet.security_public.availability_zone]
  db_az_names       = [aws_subnet.security_db_a.availability_zone, aws_subnet.security_db_b.availability_zone]

  # Loki / Promtail release, with SHA-256 checksums pinned from the upstream
  # release's SHA256SUMS file. Bump the version and the hashes together.
  loki_version    = "2.8.2"
  loki_sha256     = "ed5582a8945e7b215932d196f474f812db07cb92db3685c5fbd95300414e0918"
  promtail_sha256 = "f3476f30dfe00168c84e46bc51a58e02304e9b4b43fbd97ad98b6d54e2293d59"

  # Fixed address so spoke user-data can reference Loki without a dependency cycle.
  siem_private_ip = cidrhost(cidrsubnet(local.security_cidr, 8, 0), 10)
  loki_push_url   = "http://${local.siem_private_ip}:3100/loki/api/v1/push"

  # Rendered once and handed to every web tier (spokes + Tokyo).
  web_user_data = templatefile("${path.module}/scripts/promtail-web.sh.tftpl", {
    loki_push_url   = local.loki_push_url
    loki_version    = local.loki_version
    promtail_sha256 = local.promtail_sha256
  })
}
