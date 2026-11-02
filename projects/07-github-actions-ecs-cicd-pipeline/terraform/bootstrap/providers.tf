provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "p07-ecs-cicd"
      Environment = "shared"
      ManagedBy   = "terraform"
    }
  }
}
