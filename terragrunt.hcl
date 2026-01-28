# Terragrunt configuration for Rules Engine Framework
# This is the root terragrunt.hcl that deploys everything as a single module

include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "${get_parent_terragrunt_dir()}/terraform"
}

# Generate provider configuration
generate "provider" {
  path      = "provider_override.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}
EOF
}

# Inputs from terragrunt.hcl or environment
inputs = {
  project_name = "rules-engine"
  environment  = "dev"
  aws_region   = "us-east-1"

  # Database Configuration
  database_name     = "rules_engine"
  database_username = "rulesadmin"
  # database_password will be auto-generated if not provided

  database_instance_class = "db.r6g.large"
  database_instance_count = 2
  database_engine_version = "15.4"
  database_backup_retention = 7
  database_storage_encrypted = true

  # Networking - These MUST be provided
  # vpc_id = "vpc-xxxxxxxxx"
  # database_subnet_ids = ["subnet-xxx", "subnet-yyy"]

  # S3 Configuration
  enable_s3_versioning = true
  enable_s3_encryption = true

  # Glue Configuration
  glue_worker_type     = "G.1X"
  glue_number_of_workers = 2
  glue_version         = "4.0"

  # API Gateway Configuration
  enable_api_cors = true
  api_cors_origins = ["*"]

  # EventBridge Schedules
  eventbridge_schedules = {
    daily_validation = "cron(0 2 * * ? *)"
  }

  # Monitoring
  enable_cloudwatch_alarms = true
}
