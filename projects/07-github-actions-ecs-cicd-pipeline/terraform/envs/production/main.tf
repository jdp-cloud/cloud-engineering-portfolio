module "stack" {
  source = "../../modules/ecs-service-stack"

  environment = "production"
  region      = "us-east-1"
  vpc_cidr    = "10.80.0.0/16"
  public_subnets = {
    a = {
      cidr = "10.80.0.0/24"
      az   = "us-east-1a"
    }
    b = {
      cidr = "10.80.1.0/24"
      az   = "us-east-1b"
    }
  }
  allowed_ingress_cidrs = var.allowed_ingress_cidrs
  api_image             = var.api_image
  web_image             = var.web_image
}
