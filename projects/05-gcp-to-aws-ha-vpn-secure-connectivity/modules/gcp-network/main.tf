# GCP side of the network: custom-mode VPC, one subnet, HA VPN gateway,
# the Cloud Router that speaks BGP to AWS, and an optional private test VM.

locals {
  test_tag = "${var.name_prefix}-test"
}

resource "google_compute_network" "this" {
  name                    = "${var.name_prefix}-vpc"
  auto_create_subnetworks = false
  routing_mode            = "GLOBAL"
}

resource "google_compute_subnetwork" "this" {
  name                     = "${var.name_prefix}-subnet"
  region                   = var.region
  network                  = google_compute_network.this.id
  ip_cidr_range            = var.subnet_cidr
  private_ip_google_access = true

  dynamic "log_config" {
    for_each = var.enable_flow_logs ? [1] : []
    content {
      aggregation_interval = "INTERVAL_5_SEC"
      flow_sampling        = 0.5
      metadata             = "INCLUDE_ALL_METADATA"
    }
  }
}

# ---------------------------------------------------------------------------
# HA VPN gateway (two interfaces, each with its own external IP) and the
# Cloud Router that exchanges routes with AWS over BGP.
# ---------------------------------------------------------------------------
resource "google_compute_ha_vpn_gateway" "this" {
  name       = "${var.name_prefix}-ha-vpn-gw"
  region     = var.region
  network    = google_compute_network.this.id
  stack_type = "IPV4_ONLY"
}

resource "google_compute_router" "vpn" {
  name    = "${var.name_prefix}-vpn-router"
  region  = var.region
  network = google_compute_network.this.id

  bgp {
    asn            = var.router_asn
    advertise_mode = "DEFAULT" # advertises the subnet ranges of this VPC
  }
}

# ---------------------------------------------------------------------------
# Private test VM. No external IP, shielded VM, OS Login, dedicated service
# account with no roles. Outbound package installs go through Cloud NAT
# (egress only); administration goes through IAP TCP forwarding.
# ---------------------------------------------------------------------------
resource "google_service_account" "vm" {
  count = var.enable_test_vm ? 1 : 0

  account_id   = "${var.name_prefix}-vm"
  display_name = "HA VPN test VM (no roles)"
}

resource "google_compute_router" "nat" {
  count = var.enable_test_vm ? 1 : 0

  name    = "${var.name_prefix}-nat-router"
  region  = var.region
  network = google_compute_network.this.id
}

resource "google_compute_router_nat" "this" {
  count = var.enable_test_vm ? 1 : 0

  name                               = "${var.name_prefix}-nat"
  router                             = google_compute_router.nat[0].name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Only the AWS VPC may reach the VM (ICMP + iperf3), and only Google's IAP
# range may reach SSH. Nothing is open to 0.0.0.0/0.
resource "google_compute_firewall" "allow_from_aws" {
  count = var.enable_test_vm ? 1 : 0

  name          = "${var.name_prefix}-allow-from-aws"
  network       = google_compute_network.this.name
  direction     = "INGRESS"
  source_ranges = [var.remote_cidr]
  target_tags   = [local.test_tag]

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["5201"]
  }

  allow {
    protocol = "udp"
    ports    = ["5201"]
  }
}

resource "google_compute_firewall" "allow_iap_ssh" {
  count = var.enable_test_vm ? 1 : 0

  name          = "${var.name_prefix}-allow-iap-ssh"
  network       = google_compute_network.this.name
  direction     = "INGRESS"
  source_ranges = ["35.235.240.0/20"] # IAP TCP forwarding range
  target_tags   = [local.test_tag]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

resource "google_compute_instance" "test" {
  # checkov:skip=CKV_GCP_38: disposable lab VM holding no data; Google-managed encryption at rest is sufficient (CSEK/CMEK is a production hardening step)
  count = var.enable_test_vm ? 1 : 0

  name         = "${var.name_prefix}-test-vm"
  machine_type = "e2-micro"
  zone         = var.zone
  tags         = [local.test_tag]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.this.id
    # No access_config block: the VM has no external IP.
  }

  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  service_account {
    email  = google_service_account.vm[0].email
    scopes = ["cloud-platform"] # scope only; the account holds no IAM roles
  }

  metadata = {
    enable-oslogin         = "TRUE"
    block-project-ssh-keys = "TRUE"
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    set -euo pipefail
    apt-get update -y
    DEBIAN_FRONTEND=noninteractive apt-get install -y iperf3
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

  depends_on = [google_compute_router_nat.this]
}
