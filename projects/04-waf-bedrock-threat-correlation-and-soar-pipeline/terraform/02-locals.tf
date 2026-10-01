locals {
  name_prefix = "${var.resource_prefix}-${var.environment}"

  common_tags = {
    Environment = var.environment
    Lab         = "12B"
    ManagedBy   = "Terraform"
    Project     = "Armageddon 2"
  }

  function_names = {
    application = "${local.name_prefix}-protected-api"
    analyzer    = "${local.name_prefix}-waf-analyzer"
    correlation = "${local.name_prefix}-threat-correlation"
  }

  table_names = {
    compliance_evidence  = "${local.name_prefix}-compliance-evidence"
    correlation_findings = "${local.name_prefix}-waf-correlation-findings"
    waf_events           = "${local.name_prefix}-waf-events"
  }
}
