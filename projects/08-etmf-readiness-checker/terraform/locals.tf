data "aws_caller_identity" "current" {}

locals {
  bucket_name            = "p08-etmf-readiness-${data.aws_caller_identity.current.account_id}"
  cloudtrail_bucket_name = "p08-etmf-cloudtrail-${data.aws_caller_identity.current.account_id}"
  trail_name             = "p08-etmf-data-events"
  checker_name           = "p08-etmf-checker"
  classifier_name        = "p08-etmf-classifier"
}
