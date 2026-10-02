# No credentials appear in this repo.
#   AWS:    standard credential chain (SSO profile, env vars, or aws_profile).
#   Google: Application Default Credentials -> `gcloud auth application-default login`
#           (never a downloaded service-account JSON key).

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project   = "gcp-to-aws-ha-vpn"
      Phase     = "01-ha-vpn"
      ManagedBy = "terraform"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
}
