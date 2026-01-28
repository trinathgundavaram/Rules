# Lambda Function Module

# Create a temporary directory with Lambda code and shared libraries
locals {
  lambda_source_dir = "${path.module}/scripts/${var.lambda_name}"
  shared_libs_dir   = "${path.module}/../../shared"
  package_dir       = "${path.module}/.packages/${var.lambda_name}"
}

# Copy Lambda code and shared libraries to package directory
resource "null_resource" "prepare_lambda_package" {
  triggers = {
    lambda_code_hash = sha256(join("", [
      for f in fileset(local.lambda_source_dir, "**") : 
      fileexists("${local.lambda_source_dir}/${f}") ? filesha256("${local.lambda_source_dir}/${f}") : ""
    ]))
    shared_libs_hash = sha256(join("", [
      for f in fileset(local.shared_libs_dir, "**/*.py") : 
      fileexists("${local.shared_libs_dir}/${f}") ? filesha256("${local.shared_libs_dir}/${f}") : ""
    ]))
  }

  provisioner "local-exec" {
    command = <<-EOT
      mkdir -p ${local.package_dir}
      if [ -d "${local.lambda_source_dir}" ]; then
        cp -r ${local.lambda_source_dir}/* ${local.package_dir}/ 2>/dev/null || true
      fi
      if [ -d "${local.shared_libs_dir}" ]; then
        cp -r ${local.shared_libs_dir}/* ${local.package_dir}/ 2>/dev/null || true
      fi
    EOT
  }
}

# Create ZIP archive
data "archive_file" "lambda_zip" {
  depends_on = [null_resource.prepare_lambda_package]
  
  type        = "zip"
  source_dir  = local.package_dir
  output_path = var.output_path
  
  excludes = [
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    "*.pyc",
    "*.md",
    "*.txt",
    ".git*"
  ]
}

resource "aws_lambda_function" "main" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = var.function_name
  role            = var.iam_role_arn
  handler         = var.handler
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = var.runtime
  timeout         = var.timeout
  memory_size     = var.memory_size
  description     = var.description

  environment {
    variables = var.environment_variables
  }

  dynamic "vpc_config" {
    for_each = var.vpc_config != null ? [1] : []
    content {
      subnet_ids         = var.vpc_config.subnet_ids
      security_group_ids = var.vpc_config.security_group_ids
    }
  }

  tags = merge(var.tags, {
    Name = var.function_name
  })

  depends_on = [
    data.archive_file.lambda_zip
  ]
}

resource "aws_lambda_function_event_invoke_config" "main" {
  function_name = aws_lambda_function.main.function_name

  maximum_retry_attempts = var.max_retry_attempts
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}
