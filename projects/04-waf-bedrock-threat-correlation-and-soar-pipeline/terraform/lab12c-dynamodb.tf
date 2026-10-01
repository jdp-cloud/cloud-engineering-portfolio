resource "aws_dynamodb_table" "compliance_evidence" {
  name         = local.table_names.compliance_evidence
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "evidence_id"

  attribute {
    name = "evidence_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  tags = merge(
    local.common_tags,
    {
      Lab     = "12C"
      Purpose = "Compliance evidence"
    }
  )
}
