resource "random_password" "db" {
  length  = 32
  special = false # keeps the password URL-safe inside DATABASE_URL
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-db"
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_db_instance" "main" {
  identifier     = "${var.project}-db"
  engine         = "postgres"
  engine_version = "15" # matches local docker-compose and CI
  instance_class = var.db_instance_class

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = "trading_portfolio"
  username = "trading_admin"
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period    = 1
  auto_minor_version_upgrade = true
  apply_immediately          = true

  # Demo environment: allow clean `terraform destroy` with no leftover (billable) snapshot
  skip_final_snapshot = true
  deletion_protection = false
}

locals {
  database_url = "postgresql://${aws_db_instance.main.username}:${random_password.db.result}@${aws_db_instance.main.address}:${aws_db_instance.main.port}/${aws_db_instance.main.db_name}"
}
