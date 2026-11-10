resource "aws_s3_bucket" "etmf" {
  bucket        = local.bucket_name
  force_destroy = var.force_destroy
}

resource "aws_s3_bucket_ownership_controls" "etmf" {
  bucket = aws_s3_bucket.etmf.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "etmf" {
  bucket = aws_s3_bucket.etmf.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "etmf" {
  bucket = aws_s3_bucket.etmf.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "etmf" {
  bucket = aws_s3_bucket.etmf.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = false
  }
}

data "aws_iam_policy_document" "etmf" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.etmf.arn,
      "${aws_s3_bucket.etmf.arn}/*",
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "etmf" {
  bucket = aws_s3_bucket.etmf.id
  policy = data.aws_iam_policy_document.etmf.json

  depends_on = [aws_s3_bucket_public_access_block.etmf]
}

resource "aws_s3_object" "rules" {
  bucket                 = aws_s3_bucket.etmf.id
  key                    = "config/expected_artifacts.yaml"
  source                 = "${path.module}/../config/expected_artifacts.yaml"
  etag                   = filemd5("${path.module}/../config/expected_artifacts.yaml")
  content_type           = "text/yaml"
  server_side_encryption = "AES256"

  depends_on = [
    aws_s3_bucket_versioning.etmf,
    aws_s3_bucket_server_side_encryption_configuration.etmf,
    aws_s3_bucket_public_access_block.etmf,
  ]
}

resource "aws_s3_object" "milestones" {
  bucket                 = aws_s3_bucket.etmf.id
  key                    = "config/site_milestones.csv"
  source                 = "${path.module}/../data/site_milestones.csv"
  etag                   = filemd5("${path.module}/../data/site_milestones.csv")
  content_type           = "text/csv"
  server_side_encryption = "AES256"

  depends_on = [
    aws_s3_bucket_versioning.etmf,
    aws_s3_bucket_server_side_encryption_configuration.etmf,
    aws_s3_bucket_public_access_block.etmf,
  ]
}

resource "aws_s3_object" "sample_index" {
  count = var.upload_sample_index ? 1 : 0

  bucket                 = aws_s3_bucket.etmf.id
  key                    = "incoming/etmf_index.csv"
  source                 = "${path.module}/../data/etmf_index.csv"
  etag                   = filemd5("${path.module}/../data/etmf_index.csv")
  content_type           = "text/csv"
  server_side_encryption = "AES256"

  # Upload after the notification exists so the first apply runs the checker,
  # and after the rule files exist so that run can read them.
  depends_on = [
    aws_s3_bucket_notification.incoming,
    aws_s3_object.rules,
    aws_s3_object.milestones,
  ]
}
