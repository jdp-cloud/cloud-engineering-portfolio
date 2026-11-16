data "aws_caller_identity" "current" {}

# Bootstrap creates these repositories. Apply bootstrap before planning here.
data "aws_ecr_repository" "web" {
  name = "p07-web"
}

data "aws_ecr_repository" "api" {
  name = "p07-api"
}
