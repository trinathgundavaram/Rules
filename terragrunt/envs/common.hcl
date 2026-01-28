# Common configuration shared across all environments

inputs = {
  project_name = "rules-engine"
  
  # Common database settings
  database_name     = "rules_engine"
  database_username = "rulesadmin"
  database_engine_version = "15.4"
  database_storage_encrypted = true

  # Common S3 settings
  enable_s3_versioning = true
  enable_s3_encryption = true

  # Common API settings
  enable_api_cors = true
  api_cors_origins = ["*"]

  # Common EventBridge schedules
  eventbridge_schedules = {
    daily_validation = "cron(0 2 * * ? *)"
  }
}
