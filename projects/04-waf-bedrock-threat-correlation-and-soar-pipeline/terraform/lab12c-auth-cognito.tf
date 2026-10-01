# ============================================================
# Lab D Enhancement: Amazon Cognito Authentication
# ============================================================
#
# Cognito provides user authentication for the Lab 12C
# protected API. API Gateway integration is added separately
# after the identity infrastructure validates successfully.
#
# The application client intentionally has no client secret.
# This supports the USER_PASSWORD_AUTH lab workflow without
# requiring SECRET_HASH handling.
# ============================================================

resource "aws_cognito_user_pool" "application" {
  name = "${local.name_prefix}-user-pool"

  mfa_configuration = "ON"

  software_token_mfa_configuration {
    enabled = true
  }

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  username_configuration {
    case_sensitive = false
  }

  password_policy {
    minimum_length                   = 12
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 1
  }
}

resource "aws_cognito_user_pool_client" "application" {
  name         = "${local.name_prefix}-client"
  user_pool_id = aws_cognito_user_pool.application.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  auth_session_validity = 15

  access_token_validity  = 1
  id_token_validity      = 1
  refresh_token_validity = 1

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  enable_token_revocation       = true
  prevent_user_existence_errors = "ENABLED"
}

# ============================================================
# API Gateway Cognito Authorizer
# ============================================================

resource "aws_api_gateway_authorizer" "cognito" {
  name            = "${local.name_prefix}-cognito-authorizer"
  rest_api_id     = aws_api_gateway_rest_api.application.id
  type            = "COGNITO_USER_POOLS"
  provider_arns   = [aws_cognito_user_pool.application.arn]
  identity_source = "method.request.header.Authorization"
}

# ============================================================
# Lab E Enhancement: Cognito RBAC Groups
# ============================================================
#
# Cognito group membership is included in the authenticated
# user's JWT as the cognito:groups claim. The protected Lambda
# uses that claim to make the application authorization decision.
# ============================================================

resource "aws_cognito_user_group" "security_viewers" {
  name         = "security-viewers"
  user_pool_id = aws_cognito_user_pool.application.id
  description  = "Authenticated users with read-only identity but no access to the analysis operation."
  precedence   = 30
}

resource "aws_cognito_user_group" "security_analysts" {
  name         = "security-analysts"
  user_pool_id = aws_cognito_user_pool.application.id
  description  = "Security analysts permitted to invoke the protected analysis operation."
  precedence   = 20
}

resource "aws_cognito_user_group" "security_admins" {
  name         = "security-admins"
  user_pool_id = aws_cognito_user_pool.application.id
  description  = "Security administrators permitted to invoke the protected analysis operation."
  precedence   = 10
}
