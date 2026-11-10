provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "08-etmf-readiness-checker"
      ManagedBy = "terraform"
    }
  }
}
