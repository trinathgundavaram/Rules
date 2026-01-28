# AWS Glue Job Module

# Upload Glue scripts to S3
resource "aws_s3_object" "glue_scripts" {
  for_each = fileset("${path.module}/scripts", "**/*.py")
  
  bucket = var.code_bucket
  key    = "glue/scripts/${each.value}"
  source = "${path.module}/scripts/${each.value}"
  
  etag = filemd5("${path.module}/scripts/${each.value}")
  
  tags = var.tags
}

# Upload shared libraries to S3
resource "aws_s3_object" "glue_shared_libs" {
  for_each = fileset("${path.module}/../../shared", "**/*.py")
  
  bucket = var.code_bucket
  key    = "glue/shared/${each.value}"
  source = "${path.module}/../../shared/${each.value}"
  
  etag = filemd5("${path.module}/../../shared/${each.value}")
  
  tags = var.tags
}

resource "aws_glue_job" "main" {
  name     = var.job_name
  role_arn = var.glue_role_arn

  command {
    script_location = "s3://${var.code_bucket}/glue/scripts/${var.script_name}"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"       = "python"
    "--job-bookmark-option" = "job-bookmark-enable"
    "--TempDir"            = "s3://${var.temp_bucket}/glue-temp/"
    "--enable-metrics"     = "true"
    "--enable-spark-ui"    = "true"
    "--spark-event-logs-path" = "s3://${var.temp_bucket}/spark-logs/"
    "--extra-py-files"     = "s3://${var.code_bucket}/glue/shared/"
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

  depends_on = [
    aws_s3_object.glue_scripts,
    aws_s3_object.glue_shared_libs
  ]
}

resource "aws_cloudwatch_log_group" "glue" {
  name              = "/aws-glue/jobs/${var.job_name}"
  retention_in_days = 14

  tags = var.tags
}
