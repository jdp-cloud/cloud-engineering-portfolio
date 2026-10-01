variable "admin_uri_keywords" {
  description = "URI keywords that increase deterministic correlation risk scores"
  type        = list(string)

  default = [
    "admin",
    "login",
    "signin",
    "auth",
    "token",
    "cognito",
  ]
}

variable "analyzer_lookback_minutes" {
  description = "Number of recent minutes the analyzer reads from the WAF log group"
  type        = number
  default     = 10

  validation {
    condition = (
      var.analyzer_lookback_minutes >= 1 &&
      var.analyzer_lookback_minutes <= 60
    )
    error_message = "Analyzer lookback must be between 1 and 60 minutes."
  }
}

variable "aws_region" {
  description = "AWS Region used for the standalone Lab 12 deployment"
  type        = string
  default     = "us-east-1"
}

variable "bedrock_model_id" {
  description = "Amazon Bedrock model or inference profile ID used by both analysis Lambdas"
  type        = string

  validation {
    condition     = length(trimspace(var.bedrock_model_id)) > 0
    error_message = "bedrock_model_id must not be empty."
  }
}

variable "correlation_window_minutes" {
  description = "Time window used when correlating stored WAF events"
  type        = number
  default     = 60

  validation {
    condition = (
      var.correlation_window_minutes >= 1 &&
      var.correlation_window_minutes <= 1440
    )
    error_message = "Correlation window must be between 1 and 1440 minutes."
  }
}

variable "enable_point_in_time_recovery" {
  description = "Enable DynamoDB point-in-time recovery; disabled by default to limit lab cost"
  type        = bool
  default     = false
}

variable "environment" {
  description = "Environment label included in resource names and tags"
  type        = string
  default     = "dev"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.environment))
    error_message = "environment may contain only lowercase letters, numbers, and hyphens."
  }
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention period"
  type        = number
  default     = 7

  validation {
    condition = contains(
      [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365],
      var.log_retention_days
    )
    error_message = "Select a supported CloudWatch Logs retention period."
  }
}

variable "max_correlation_events" {
  description = "Maximum number of DynamoDB WAF-event records processed by one correlation run"
  type        = number
  default     = 500

  validation {
    condition = (
      var.max_correlation_events >= 1 &&
      var.max_correlation_events <= 1000
    )
    error_message = "max_correlation_events must be between 1 and 1000."
  }
}

variable "max_log_events" {
  description = "Maximum number of WAF log events read by one analyzer invocation"
  type        = number
  default     = 25

  validation {
    condition = (
      var.max_log_events >= 1 &&
      var.max_log_events <= 1000
    )
    error_message = "max_log_events must be between 1 and 1000."
  }
}

variable "minimum_event_count" {
  description = "Minimum stored WAF event count required before creating a correlation finding"
  type        = number
  default     = 3

  validation {
    condition     = var.minimum_event_count >= 1
    error_message = "minimum_event_count must be at least 1."
  }
}

variable "resource_prefix" {
  description = "Prefix used for named Lab 12 AWS resources"
  type        = string
  default     = "armageddon2-lab12"

  validation {
    condition = can(
      regex(
        "^[a-z0-9][a-z0-9-]{2,31}$",
        var.resource_prefix
      )
    )
    error_message = "resource_prefix must be 3–32 lowercase letters, numbers, or hyphens."
  }
}

variable "bedrock_resource_arns" {
  description = "Bedrock inference-profile and foundation-model ARNs permitted by Lambda IAM policies"
  type        = list(string)

  validation {
    condition = (
      length(var.bedrock_resource_arns) > 0 &&
      alltrue([
        for arn in var.bedrock_resource_arns :
        startswith(arn, "arn:")
      ])
    )
    error_message = "Provide at least one valid Bedrock resource ARN."
  }
}

variable "enable_schedules" {
  description = "Enable automatic EventBridge Scheduler invocation of the analyzer and correlation Lambdas"
  type        = bool
  default     = false
}

variable "analyzer_schedule_expression" {
  description = "EventBridge Scheduler rate or cron expression for the WAF analyzer Lambda"
  type        = string
  default     = "rate(5 minutes)"

  validation {
    condition = can(
      regex(
        "^(rate|cron)\\(.+\\)$",
        trimspace(var.analyzer_schedule_expression)
      )
    )
    error_message = "Use a valid EventBridge rate(...) or cron(...) expression."
  }
}

variable "correlation_schedule_expression" {
  description = "EventBridge Scheduler rate or cron expression for the threat-correlation Lambda"
  type        = string
  default     = "rate(1 hour)"

  validation {
    condition = can(
      regex(
        "^(rate|cron)\\(.+\\)$",
        trimspace(var.correlation_schedule_expression)
      )
    )
    error_message = "Use a valid EventBridge rate(...) or cron(...) expression."
  }
}

variable "notification_email" {
  description = "Email endpoint subscribed to Lab 12A SNS notification topics"
  type        = string
  sensitive   = true

  validation {
    condition = can(
      regex(
        "^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$",
        var.notification_email
      )
    )

    error_message = "notification_email must be a valid email address."
  }
}
