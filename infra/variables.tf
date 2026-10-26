variable "project" {
  description = "Name prefix for all resources"
  type        = string
  default     = "trading-portfolio"
}

variable "region" {
  description = "AWS region (this account is restricted to us-east-2)"
  type        = string
  default     = "us-east-2"
}

variable "instance_type" {
  description = "EC2 instance type for the backend (free-tier eligible, x86)"
  type        = string
  default     = "t3.small"
}

variable "db_instance_class" {
  description = "RDS instance class (free-tier eligible)"
  type        = string
  default     = "db.t4g.micro"
}

variable "alpha_vantage_api_key" {
  description = "Optional Alpha Vantage key used as a fallback quote source"
  type        = string
  default     = ""
  sensitive   = true
}
