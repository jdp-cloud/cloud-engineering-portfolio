# Stores normalized WAF events. The analyzer uses a deterministic event_id
# and a conditional PutItem to prevent duplicate records.
resource "aws_dynamodb_table" "waf_events" {
  name         = local.table_names.waf_events
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "event_id"

  attribute {
    name = "event_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
}

# Stores correlation results for later analyst and SOAR processing.
resource "aws_dynamodb_table" "correlation_findings" {
  name         = local.table_names.correlation_findings
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "finding_id"

  attribute {
    name = "finding_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
}
