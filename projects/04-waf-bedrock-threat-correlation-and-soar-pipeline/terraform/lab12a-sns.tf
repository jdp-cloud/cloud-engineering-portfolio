# General notifications produced by the SOAR response Lambda.
resource "aws_sns_topic" "soar_notifications" {
  name = "${local.name_prefix}-soar-notifications"

  tags = local.common_tags
}

# Direct EventBridge alert path for CRITICAL findings.
resource "aws_sns_topic" "critical_alerts" {
  name = "${local.name_prefix}-critical-alerts"

  tags = local.common_tags
}

# Permit only the CRITICAL EventBridge rule to publish directly to this topic.
data "aws_iam_policy_document" "critical_alerts" {
  statement {
    sid     = "AllowCriticalEventBridgeRule"
    effect  = "Allow"
    actions = ["sns:Publish"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    resources = [
      aws_sns_topic.critical_alerts.arn,
    ]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values = [
        aws_cloudwatch_event_rule.critical_finding.arn,
      ]
    }
  }
}

resource "aws_sns_topic_policy" "critical_alerts" {
  arn    = aws_sns_topic.critical_alerts.arn
  policy = data.aws_iam_policy_document.critical_alerts.json
}

# Email delivery for normal SOAR incident notifications.
resource "aws_sns_topic_subscription" "soar_email" {
  topic_arn = aws_sns_topic.soar_notifications.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# Immediate email delivery for CRITICAL findings.
resource "aws_sns_topic_subscription" "critical_email" {
  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "email"
  endpoint  = var.notification_email
}
