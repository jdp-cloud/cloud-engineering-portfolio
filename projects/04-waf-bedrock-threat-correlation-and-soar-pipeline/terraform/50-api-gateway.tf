resource "aws_api_gateway_rest_api" "application" {
  name        = "${local.name_prefix}-api"
  description = "Protected REST API used to generate AWS WAF telemetry"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "analyze" {
  rest_api_id = aws_api_gateway_rest_api.application.id
  parent_id   = aws_api_gateway_rest_api.application.root_resource_id
  path_part   = "analyze"
}

# The client sends GET, while API Gateway invokes Lambda internally
# with POST as required by the Lambda proxy integration contract.
resource "aws_api_gateway_method" "analyze_get" {
  rest_api_id   = aws_api_gateway_rest_api.application.id
  resource_id   = aws_api_gateway_resource.analyze.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "analyze_get" {
  rest_api_id = aws_api_gateway_rest_api.application.id
  resource_id = aws_api_gateway_resource.analyze.id
  http_method = aws_api_gateway_method.analyze_get.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.application.invoke_arn
}

resource "aws_api_gateway_deployment" "application" {
  rest_api_id = aws_api_gateway_rest_api.application.id
  description = "Lab 12 protected API deployment"

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.analyze.id,
      aws_api_gateway_authorizer.cognito.id,
      aws_api_gateway_method.analyze_get.id,
      aws_api_gateway_integration.analyze_get.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "application" {
  rest_api_id   = aws_api_gateway_rest_api.application.id
  deployment_id = aws_api_gateway_deployment.application.id
  stage_name    = var.environment

  description = "Lab 12 ${var.environment} API stage"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.application.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = join(
    "",
    [
      aws_api_gateway_stage.application.execution_arn,
      "/",
      aws_api_gateway_method.analyze_get.http_method,
      aws_api_gateway_resource.analyze.path,
    ]
  )
}
