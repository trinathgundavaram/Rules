# Rules Engine Framework - Outputs

output "database_endpoint" {
  description = "Aurora PostgreSQL endpoint"
  value       = module.database.endpoint
  sensitive   = false
}

output "database_port" {
  description = "Aurora PostgreSQL port"
  value       = module.database.port
}

output "database_name" {
  description = "Database name"
  value       = var.database_name
}

output "database_secret_arn" {
  description = "ARN of the database secret in Secrets Manager"
  value       = module.secrets.database_secret_arn
}

output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_url
}

output "lambda_rule_executor_arn" {
  description = "ARN of the rule executor Lambda function"
  value       = module.lambda_rule_executor.function_arn
}

output "lambda_api_gateway_arn" {
  description = "ARN of the API Gateway Lambda function"
  value       = module.lambda_api_gateway.function_arn
}

output "glue_job_name" {
  description = "Name of the Glue job"
  value       = module.glue.job_name
}

output "s3_results_bucket" {
  description = "S3 bucket for validation results"
  value       = module.s3.results_bucket_name
}

output "s3_temp_bucket" {
  description = "S3 bucket for temporary files"
  value       = module.s3.temp_bucket_name
}

output "s3_code_bucket" {
  description = "S3 bucket for code artifacts"
  value       = module.s3.code_bucket_name
}

output "iam_lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = module.iam.lambda_execution_role_arn
}

output "iam_glue_role_arn" {
  description = "ARN of the Glue execution role"
  value       = module.iam.glue_role_arn
}
