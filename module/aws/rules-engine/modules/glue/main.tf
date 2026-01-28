# AWS Glue Job Module

resource "aws_glue_job" "main" {
  name     = var.job_name
  role_arn = var.glue_role_arn

  command {
    script_location = var.script_path
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"       = "python"
    "--job-bookmark-option" = "job-bookmark-enable"
    "--TempDir"            = "s3://${var.temp_bucket}/glue-temp/"
    "--enable-metrics"     = "true"
    "--enable-spark-ui"    = "true"
    "--spark-event-logs-path" = "s3://${var.temp_bucket}/spark-logs/"
  }

  execution_property {
    max_concurrent_runs = 3
  }

  glue_version = var.glue_version

  max_retries = 2
  timeout     = 2880  # 48 hours

  worker_type     = var.worker_type
  number_of_workers = var.number_of_workers

  tags = merge(var.tags, {
    Name = var.job_name
  })
}

resource "aws_cloudwatch_log_group" "glue" {
  name              = "/aws-glue/jobs/${var.job_name}"
  retention_in_days = 14

  tags = var.tags
}
