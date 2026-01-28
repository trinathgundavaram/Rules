# Root Terragrunt Configuration
# This file defines common settings for all environments

# Configure Terragrunt to automatically store tfstate files in S3
remote_state {
  backend = "s3"
  config = {
    bucket         = get_env("TF_STATE_BUCKET", "your-terraform-state-bucket")
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = get_env("AWS_REGION", "us-east-1")
    encrypt        = true
    dynamodb_table = get_env("TF_STATE_LOCK_TABLE", "terraform-state-lock")
  }

  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
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

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "RulesEngine"
      Environment = var.environment
      ManagedBy   = "Terragrunt"
    }
  }
}
EOF
}

# Include common inputs
include "common" {
  path = "${get_terragrunt_dir()}/envs/common.hcl"
}
