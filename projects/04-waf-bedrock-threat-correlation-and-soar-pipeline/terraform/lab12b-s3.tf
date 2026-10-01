resource "aws_s3_bucket" "executive_reports" {
  bucket        = local.report_bucket_name
  force_destroy = var.report_bucket_force_destroy

  lifecycle {
    precondition {
      condition = (
        length(local.report_bucket_name) >= 3 &&
        length(local.report_bucket_name) <= 63
      )
      error_message = "The generated executive-report bucket name must contain 3–63 characters."
    }
  }

  tags = merge(
    local.common_tags,
    {
      Purpose = "Executive security reports"
    }
  )
}

resource "aws_s3_bucket_ownership_controls" "executive_reports" {
  bucket = aws_s3_bucket.executive_reports.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "executive_reports" {
  bucket = aws_s3_bucket.executive_reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "executive_reports" {
  bucket = aws_s3_bucket.executive_reports.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }

    bucket_key_enabled = false
  }
}

resource "aws_s3_bucket_versioning" "executive_reports" {
  bucket = aws_s3_bucket.executive_reports.id

  versioning_configuration {
    status = "Enabled"
  }
}

data "aws_iam_policy_document" "executive_reports_bucket" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    actions = ["s3:*"]

    resources = [
      aws_s3_bucket.executive_reports.arn,
      "${aws_s3_bucket.executive_reports.arn}/*",
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

resource "aws_s3_bucket_policy" "executive_reports" {
  bucket = aws_s3_bucket.executive_reports.id
  policy = data.aws_iam_policy_document.executive_reports_bucket.json

  depends_on = [
    aws_s3_bucket_public_access_block.executive_reports,
  ]
}
