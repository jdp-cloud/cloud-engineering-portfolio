# Each Lambda receives a separate deployment package so source changes
# are tracked independently through source_code_hash.
data "archive_file" "analyzer" {
  type        = "zip"
  output_path = "${path.module}/waf-bedrock-analyzer.zip"

  source {
    content = file(
      "${path.module}/../src/waf_bedrock_analyzer.py"
    )
    filename = "waf_bedrock_analyzer.py"
  }
}

data "archive_file" "correlation" {
  type        = "zip"
  output_path = "${path.module}/waf-threat-correlation.zip"

  source {
    content = file(
      "${path.module}/../src/waf_threat_correlation_agent.py"
    )
    filename = "waf_threat_correlation_agent.py"
  }
}

data "archive_file" "application" {
  type        = "zip"
  output_path = "${path.module}/protected-api.zip"

  source {
    content = file(
      "${path.module}/../src/protected_api_handler.py"
    )
    filename = "protected_api_handler.py"
  }
}
