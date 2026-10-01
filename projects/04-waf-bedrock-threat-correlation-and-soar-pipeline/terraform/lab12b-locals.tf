locals {
  executive_dashboard_function_name = "${local.name_prefix}-executive-dashboard"

  report_bucket_name = lower(
    join(
      "-",
      [
        local.name_prefix,
        var.aws_region,
        data.aws_caller_identity.current.account_id,
        "reports",
      ]
    )
  )
}
