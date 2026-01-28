# Production Environment Configuration

include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "${get_parent_terragrunt_dir()}/../terraform"
}

inputs = {
  environment = "prod"
  aws_region  = "us-east-1"

  # Production-specific overrides
  database_instance_class = "db.r6g.xlarge"  # Larger for prod
  database_instance_count = 2                # Multi-AZ for prod
  database_backup_retention = 30             # Longer retention

  glue_worker_type     = "G.2X"
  glue_number_of_workers = 10                # More workers for prod

  enable_cloudwatch_alarms = true
  # alert_sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:prod-alerts"

  # Production networking - MUST be provided
  # vpc_id = "vpc-xxxxxxxxx"
  # database_subnet_ids = ["subnet-xxx", "subnet-yyy"]
  # lambda_subnet_ids = ["subnet-xxx", "subnet-yyy"]
}
