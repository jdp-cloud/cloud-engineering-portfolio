# Scan target for the Trivy IaC stage. This project NEVER runs terraform init, plan or apply on it:
# there is no AWS stage, no cloud credential and no backend. Copied from the earlier Jenkins/Terraform
# exercise (a hardened S3 bucket with a customer-managed KMS key) so the scanner has real IaC to read.

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state so the destroy stage (and any later run) can find the resources.
  # Create the bucket once, outside this config, then uncomment:
  # backend "s3" {
  #   bucket       = "<your-state-bucket>"
  #   key          = "jenkins-pipeline/terraform.tfstate"
  #   region       = "us-west-2"
  #   use_lockfile = true   # S3-native locking (Terraform >= 1.10); else use a DynamoDB table
  #   encrypt      = true
  # }
}

variable "aws_region" {
  type    = string
  default = "us-west-2"
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "jenkins-terraform-pipeline"
      ManagedBy = "terraform"
    }
  }
}

resource "aws_kms_key" "bucket" {
  description             = "Key for the pipeline demo bucket"
  enable_key_rotation     = true
  deletion_window_in_days = 7
}

resource "aws_s3_bucket" "this" {
  bucket_prefix = "jenkins-bucket-"
  force_destroy = true # lab only - remove for anything holding real data

  tags = {
    Name = "Jenkins Bucket"
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.bucket.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}

output "bucket_name" {
  value = aws_s3_bucket.this.id
}
