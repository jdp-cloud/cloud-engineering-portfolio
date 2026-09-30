# One provider alias per region. Tokyo is the hub; the other six are spokes.
# NOTE: Hong Kong (ap-east-1) is an opt-in region and must be enabled in the
# AWS account before this configuration can be applied.

locals {
  common_tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}

provider "aws" {
  alias  = "tokyo"
  region = "ap-northeast-1"
  default_tags { tags = local.common_tags }
}

provider "aws" {
  alias  = "london"
  region = "eu-west-2"
  default_tags { tags = local.common_tags }
}

provider "aws" {
  alias  = "new_york"
  region = "us-east-1"
  default_tags { tags = local.common_tags }
}

provider "aws" {
  alias  = "sao_paulo"
  region = "sa-east-1"
  default_tags { tags = local.common_tags }
}

provider "aws" {
  alias  = "sydney"
  region = "ap-southeast-2"
  default_tags { tags = local.common_tags }
}

provider "aws" {
  alias  = "california"
  region = "us-west-1"
  default_tags { tags = local.common_tags }
}

provider "aws" {
  alias  = "hong_kong"
  region = "ap-east-1"
  default_tags { tags = local.common_tags }
}
