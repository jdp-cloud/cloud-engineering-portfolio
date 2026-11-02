terraform {
  required_version = ">= 1.10"

  # The backend block lives in this file on purpose. The repo .gitignore
  # ignores a file named backend.tf so a machine-local override is never
  # committed. The bucket already exists. This project does not create it
  # and does not manage its encryption, versioning, or policy.
  backend "s3" {
    bucket       = "terraform-state-jdpayne"
    key          = "github-actions-ecs-cicd/bootstrap/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.71.0"
    }
  }
}
