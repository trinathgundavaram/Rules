# Secrets Manager Module

resource "aws_secretsmanager_secret" "database" {
  name        = var.database_secret_name
  description = "Database credentials for Rules Engine"

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id

  secret_string = jsonencode({
    host     = var.database_host
    port     = var.database_port
    dbname   = var.database_name
    username = var.database_username
    password = var.database_password
  })
}
