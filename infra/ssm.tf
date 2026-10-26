# Runtime configuration for the backend container. The instance reads every parameter under
# /<project>/ at deploy time and passes them to the container as environment variables.

resource "random_password" "jwt_secret" {
  length  = 48
  special = false
}

resource "aws_ssm_parameter" "database_url" {
  name  = "${local.param_prefix}/DATABASE_URL"
  type  = "SecureString"
  value = local.database_url
}

resource "aws_ssm_parameter" "secret_key" {
  name  = "${local.param_prefix}/SECRET_KEY"
  type  = "SecureString"
  value = random_password.jwt_secret.result
}

resource "aws_ssm_parameter" "cors_origins" {
  name  = "${local.param_prefix}/CORS_ORIGINS"
  type  = "String"
  value = "https://${aws_cloudfront_distribution.main.domain_name}"
}

resource "aws_ssm_parameter" "alpha_vantage_api_key" {
  count = var.alpha_vantage_api_key == "" ? 0 : 1

  name  = "${local.param_prefix}/ALPHA_VANTAGE_API_KEY"
  type  = "SecureString"
  value = var.alpha_vantage_api_key
}
