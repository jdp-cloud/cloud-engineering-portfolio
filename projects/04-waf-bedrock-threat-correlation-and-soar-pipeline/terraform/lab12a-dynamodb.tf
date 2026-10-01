# Stores idempotent SOAR incident records created from correlated findings.
resource "aws_dynamodb_table" "security_incidents" {
  name         = "${local.name_prefix}-security-incidents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "incident_id"

  attribute {
    name = "incident_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  tags = local.common_tags
}
