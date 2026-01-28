# Terragrunt configuration for Rules Engine Framework
# This file is used by the shared GitHub Actions workflow

terraform {
  source = "${get_parent_terragrunt_dir()}/module/aws/rules-engine"
}

# Include common configuration if it exists
include "root" {
  path = find_in_parent_folders("terragrunt.hcl")
}

# Generate provider configuration
generate "provider" {
  path      = "provider_override.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "RulesEngine"
      Environment = var.env
      ManagedBy   = "Terraform"
      Repository  = var.repo_name
      Branch      = var.branch_name
    }
  }
}
EOF
}

# Inputs from environment variables and GitHub Actions
inputs = {
  project_name = "rules-engine"
  environment  = var.env
  aws_region   = var.region
  
  # Map Terragrunt variables to Terraform variables
  env          = var.env
  region       = var.region
  account_number = var.account_number
  repo_name    = var.repo_name
  branch_name  = var.branch_name

  # Database Configuration
  database_name     = "rules_engine_${var.env}"
  database_username = "rulesadmin"
  # database_password will be auto-generated if not provided

  database_instance_class = var.env == "prod" ? "db.r6g.xlarge" : "db.t3.medium"
  database_instance_count = 2
  database_engine_version = "15.4"
  database_backup_retention = var.env == "prod" ? 30 : 7
  database_storage_encrypted = true

  # S3 Configuration
  enable_s3_versioning = true
  enable_s3_encryption = true

  # Glue Configuration
  glue_worker_type     = var.env == "prod" ? "G.2X" : "G.1X"
  glue_number_of_workers = var.env == "prod" ? 10 : 2
  glue_version         = "4.0"

  # API Gateway Configuration
  enable_api_cors = true
  api_cors_origins = var.env == "prod" ? [] : ["*"]

  # EventBridge Schedules
  eventbridge_schedules = {
    daily_validation = "cron(0 2 * * ? *)"
  }

  # Monitoring
  enable_cloudwatch_alarms = true

  # Tags
  tags = {
    Environment = var.env
    Project     = "RulesEngine"
    ManagedBy   = "Terraform"
    Repository  = var.repo_name
    Branch      = var.branch_name
  }
}
