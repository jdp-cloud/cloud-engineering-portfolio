# ============================================================
# Lab F Enhancement: Token-Use Telemetry
# ============================================================
#
# Each authenticated client session can create a token-tracking
# record before invoking the protected API.
#
# The protected Lambda later marks the record as used after
# verifying that the token identifier belongs to the
# authenticated Cognito user.
# ============================================================

resource "aws_dynamodb_table" "token_tracking" {
  name         = "${local.name_prefix}-token-tracking"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "token_id"

  attribute {
    name = "token_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
}
