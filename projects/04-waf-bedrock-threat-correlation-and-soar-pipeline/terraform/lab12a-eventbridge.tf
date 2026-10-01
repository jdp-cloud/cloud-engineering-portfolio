data "aws_cloudwatch_event_bus" "default" {
  name = "default"
}

# MEDIUM and HIGH findings enter the normal automated SOAR workflow.
resource "aws_cloudwatch_event_rule" "medium_high_finding" {
  name        = "${local.name_prefix}-medium-high-finding"
  description = "Routes medium and high WAF findings to the SOAR response agent"

  event_pattern = jsonencode({
    source = [
      "seir.waf.correlation"
    ]

    detail-type = [
      "WAF Threat Finding Created"
    ]

    detail = {
      severity = [
        "MEDIUM",
        "HIGH",
      ]
    }
  })

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "medium_high_soar" {
  rule      = aws_cloudwatch_event_rule.medium_high_finding.name
  target_id = "SOARResponseAgent"
  arn       = aws_lambda_function.soar.arn
}

resource "aws_lambda_permission" "medium_high_soar_eventbridge" {
  statement_id  = "AllowMediumHighEventBridgeSOAR"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.soar.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.medium_high_finding.arn
}

# CRITICAL findings enter the SOAR workflow and also trigger a direct alert.
resource "aws_cloudwatch_event_rule" "critical_finding" {
  name        = "${local.name_prefix}-critical-finding"
  description = "Routes critical WAF findings to SOAR and the critical alert topic"

  event_pattern = jsonencode({
    source = [
      "seir.waf.correlation"
    ]

    detail-type = [
      "WAF Threat Finding Created"
    ]

    detail = {
      severity = [
        "CRITICAL",
      ]
    }
  })

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "critical_soar" {
  rule      = aws_cloudwatch_event_rule.critical_finding.name
  target_id = "SOARResponseAgent"
  arn       = aws_lambda_function.soar.arn
}

resource "aws_lambda_permission" "critical_soar_eventbridge" {
  statement_id  = "AllowCriticalEventBridgeSOAR"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.soar.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.critical_finding.arn
}

resource "aws_cloudwatch_event_target" "critical_alert" {
  rule      = aws_cloudwatch_event_rule.critical_finding.name
  target_id = "CriticalAlertTopic"
  arn       = aws_sns_topic.critical_alerts.arn

  depends_on = [
    aws_sns_topic_policy.critical_alerts,
  ]
}
