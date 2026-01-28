output "database_secret_arn" {
  value = aws_secretsmanager_secret.database.arn
}

output "database_secret_name" {
  value = aws_secretsmanager_secret.database.name
}
