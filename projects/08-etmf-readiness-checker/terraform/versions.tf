terraform {
  required_version = ">= 1.6"

  # State stays in this directory on purpose. The state file is gitignored.
  # A remote backend (S3 and a lock table) is a production step, described in the README.
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}
