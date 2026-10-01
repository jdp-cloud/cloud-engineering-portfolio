resource "aws_wafv2_web_acl" "application" {
  name        = "${local.name_prefix}-web-acl"
  description = "Protects the Lab 12 regional API Gateway stage"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "LabDeterministicBlock"
    priority = 0

    action {
      block {}
    }

    statement {
      byte_match_statement {
        positional_constraint = "EXACTLY"
        search_string         = "true"

        field_to_match {
          single_header {
            name = "x-lab-attack"
          }
        }

        text_transformation {
          priority = 0
          type     = "NONE"
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-lab-block"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 10

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-common-rules"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-web-acl"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_association" "application" {
  resource_arn = aws_api_gateway_stage.application.arn
  web_acl_arn  = aws_wafv2_web_acl.application.arn
}

resource "aws_wafv2_web_acl_logging_configuration" "application" {
  resource_arn = aws_wafv2_web_acl.application.arn

  log_destination_configs = [
    aws_cloudwatch_log_group.waf.arn,
  ]
}
