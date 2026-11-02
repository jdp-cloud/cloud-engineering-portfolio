resource "aws_ecr_repository" "web" {
  # checkov:skip=CKV_AWS_136: AES256 is the AWS-owned key. This lab does not use a customer-managed key.
  name                 = "p07-web"
  image_tag_mutability = "IMMUTABLE"
  # Lab teardown. Destroy has to delete the repository even when pushed
  # images are still in it. A production repository would not set this.
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_repository" "api" {
  # checkov:skip=CKV_AWS_136: AES256 is the AWS-owned key. This lab does not use a customer-managed key.
  name                 = "p07-api"
  image_tag_mutability = "IMMUTABLE"
  # Lab teardown. Destroy has to delete the repository even when pushed
  # images are still in it. A production repository would not set this.
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "web" {
  repository = aws_ecr_repository.web.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep the last 15 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 15
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep the last 15 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 15
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
