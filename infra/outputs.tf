output "app_url" {
  description = "Public HTTPS URL for the whole app"
  value       = "https://${aws_cloudfront_distribution.main.domain_name}"
}

output "cloudfront_distribution_id" {
  description = "Used by CD to invalidate cached frontend files"
  value       = aws_cloudfront_distribution.main.id
}

output "frontend_bucket" {
  description = "Upload the React build here"
  value       = aws_s3_bucket.frontend.bucket
}

output "ecr_repository_url" {
  description = "Push backend images here"
  value       = aws_ecr_repository.backend.repository_url
}

output "backend_instance_id" {
  description = "Target for SSM Run Command deploys"
  value       = aws_instance.backend.id
}

output "db_endpoint" {
  description = "RDS hostname (private; reachable only from the backend)"
  value       = aws_db_instance.main.address
}
