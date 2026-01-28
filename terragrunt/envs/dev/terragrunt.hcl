# Development Environment Configuration

include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "${get_parent_terragrunt_dir()}/../terraform"
}

inputs = {
  environment = "dev"
  aws_region  = "us-east-1"

  # Development-specific overrides
  database_instance_class = "db.t4g.medium"  # Smaller for dev
  database_instance_count = 1                # Single instance for dev
  database_backup_retention = 3             # Shorter retention

  glue_worker_type     = "G.1X"
  glue_number_of_workers = 1                # Fewer workers for dev

  enable_cloudwatch_alarms = false           # Disable alarms in dev
}
