# Rules Engine Framework - Variables

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "rules-engine"
}

variable "environment" {
  description = "Environment name (dev, test, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "test", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, test, staging, prod"
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

# ============================================================================
# DATABASE VARIABLES
# ============================================================================

variable "database_name" {
  description = "Name of the Aurora PostgreSQL database"
  type        = string
  default     = "rules_engine"
}

variable "database_username" {
  description = "Master username for Aurora PostgreSQL"
  type        = string
  default     = "rulesadmin"
}

variable "database_password" {
  description = "Master password for Aurora PostgreSQL (if null, random password will be generated)"
  type        = string
  default     = null
  sensitive   = true
}

variable "database_instance_class" {
  description = "Instance class for Aurora PostgreSQL"
  type        = string
  default     = "db.r6g.large"
}

variable "database_instance_count" {
  description = "Number of Aurora instances"
  type        = number
  default     = 2
}

variable "database_engine_version" {
  description = "Aurora PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "database_backup_retention" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "database_storage_encrypted" {
  description = "Enable storage encryption"
  type        = bool
  default     = true
}

variable "database_subnet_ids" {
  description = "Subnet IDs for Aurora PostgreSQL"
  type        = list(string)
}

variable "database_security_group_ids" {
  description = "Security group IDs for Aurora PostgreSQL"
  type        = list(string)
  default     = []
}

variable "enable_database_monitoring" {
  description = "Enable enhanced monitoring for Aurora"
  type        = bool
  default     = true
}

variable "database_monitoring_interval" {
  description = "Enhanced monitoring interval in seconds"
  type        = number
  default     = 60
}

# ============================================================================
# NETWORKING VARIABLES
# ============================================================================

variable "vpc_id" {
  description = "VPC ID for resources"
  type        = string
}

variable "lambda_subnet_ids" {
  description = "Subnet IDs for Lambda functions"
  type        = list(string)
  default     = []
}

variable "enable_lambda_vpc" {
  description = "Enable VPC configuration for Lambda functions"
  type        = bool
  default     = false
}

# ============================================================================
# S3 VARIABLES
# ============================================================================

variable "enable_s3_versioning" {
  description = "Enable versioning for S3 buckets"
  type        = bool
  default     = true
}

variable "enable_s3_encryption" {
  description = "Enable encryption for S3 buckets"
  type        = bool
  default     = true
}

# ============================================================================
# GLUE VARIABLES
# ============================================================================

variable "glue_worker_type" {
  description = "Glue worker type"
  type        = string
  default     = "G.1X"
}

variable "glue_number_of_workers" {
  description = "Number of Glue workers"
  type        = number
  default     = 2
}

variable "glue_version" {
  description = "Glue version"
  type        = string
  default     = "4.0"
}

# ============================================================================
# API GATEWAY VARIABLES
# ============================================================================

variable "enable_api_cors" {
  description = "Enable CORS for API Gateway"
  type        = bool
  default     = true
}

variable "api_cors_origins" {
  description = "Allowed CORS origins"
  type        = list(string)
  default     = ["*"]
}

# ============================================================================
# EVENTBRIDGE VARIABLES
# ============================================================================

variable "eventbridge_schedules" {
  description = "Map of schedule names to cron expressions for EventBridge rules"
  type        = map(string)
  default = {
    daily_validation = "cron(0 2 * * ? *)"  # Daily at 2 AM UTC
  }
}

# ============================================================================
# MONITORING VARIABLES
# ============================================================================

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = true
}

variable "alert_sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  type        = string
  default     = ""
}

variable "use_s3_for_lambda_code" {
  description = "Use S3 for Lambda code deployment (for packages > 50MB)"
  type        = bool
  default     = false
}
