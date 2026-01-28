# Code Deployment Resources
# This file handles automatic packaging and deployment of Lambda functions and Glue scripts

locals {
  lambda_packages_dir = "${path.module}/lambda_packages"
  source_root        = "${path.module}/../src"
}

# Create lambda_packages directory
resource "null_resource" "create_packages_dir" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "mkdir -p ${local.lambda_packages_dir}"
  }
}

# Package Lambda Rule Executor
data "archive_file" "lambda_rule_executor" {
  type        = "zip"
  source_dir  = "${local.source_root}/lambda/rule_executor"
  output_path = "${local.lambda_packages_dir}/rule_executor.zip"
  excludes    = ["__pycache__", "*.pyc", ".pytest_cache"]

  depends_on = [null_resource.create_packages_dir]
}

# Package Lambda API Gateway
data "archive_file" "lambda_api_gateway" {
  type        = "zip"
  source_dir  = "${local.source_root}/lambda/api_gateway"
  output_path = "${local.lambda_packages_dir}/api_gateway.zip"
  excludes    = ["__pycache__", "*.pyc", ".pytest_cache"]

  depends_on = [null_resource.create_packages_dir]
}

# Upload Lambda packages to S3 (for versioning and larger packages)
resource "aws_s3_object" "lambda_rule_executor_code" {
  bucket = module.s3.code_bucket_name
  key    = "lambda/rule_executor-${data.archive_file.lambda_rule_executor.output_md5}.zip"
  source = data.archive_file.lambda_rule_executor.output_path
  etag   = filemd5(data.archive_file.lambda_rule_executor.output_path)

  tags = local.common_tags

  depends_on = [
    module.s3,
    data.archive_file.lambda_rule_executor
  ]
}

resource "aws_s3_object" "lambda_api_gateway_code" {
  bucket = module.s3.code_bucket_name
  key    = "lambda/api_gateway-${data.archive_file.lambda_api_gateway.output_md5}.zip"
  source = data.archive_file.lambda_api_gateway.output_path
  etag   = filemd5(data.archive_file.lambda_api_gateway.output_path)

  tags = local.common_tags

  depends_on = [
    module.s3,
    data.archive_file.lambda_api_gateway
  ]
}

# Upload Glue scripts to S3
resource "aws_s3_object" "glue_bulk_validator" {
  bucket = module.s3.code_bucket_name
  key    = "glue/bulk_validator.py"
  source = "${local.source_root}/glue/bulk_validator.py"
  etag   = filemd5("${local.source_root}/glue/bulk_validator.py")

  tags = merge(local.common_tags, {
    Purpose = "Glue Script"
  })

  depends_on = [module.s3]
}

# Copy all Python source files to S3 for Glue to import
resource "null_resource" "upload_glue_dependencies" {
  triggers = {
    source_hash = sha256(join("", [
      for f in fileset("${local.source_root}", "**/*.py") : filesha256("${local.source_root}/${f}")
    ]))
    code_bucket = module.s3.code_bucket_name
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${local.source_root}
      aws s3 sync . s3://${module.s3.code_bucket_name}/glue/dependencies/ \
        --exclude "*.pyc" \
        --exclude "__pycache__/*" \
        --exclude ".pytest_cache/*" \
        --exclude "ui/*" \
        --exclude "lambda/*" \
        --exclude "tests/*" \
        --exclude "*.md" \
        --exclude ".git/*" \
        --region ${var.aws_region} || echo "S3 sync failed - ensure AWS CLI is configured"
    EOT
  }

  depends_on = [module.s3]
}

# Note: Lambda functions are deployed directly from local zip files
# For packages > 50MB, uncomment the S3-based deployment below
# or set use_s3_for_lambda_code = true in variables

# Update Lambda functions to use S3 code (for larger packages > 50MB)
# Uncomment if needed for large Lambda packages
# resource "null_resource" "update_lambda_from_s3" {
#   count = var.use_s3_for_lambda_code ? 1 : 0
#
#   triggers = {
#     rule_executor_hash = aws_s3_object.lambda_rule_executor_code.etag
#     api_gateway_hash   = aws_s3_object.lambda_api_gateway_code.etag
#   }
#
#   provisioner "local-exec" {
#     command = <<-EOT
#       aws lambda update-function-code \
#         --function-name ${module.lambda_rule_executor.function_name} \
#         --s3-bucket ${module.s3.code_bucket_name} \
#         --s3-key ${aws_s3_object.lambda_rule_executor_code.key} \
#         --region ${var.aws_region} || true
#
#       aws lambda update-function-code \
#         --function-name ${module.lambda_api_gateway.function_name} \
#         --s3-bucket ${module.s3.code_bucket_name} \
#         --s3-key ${aws_s3_object.lambda_api_gateway_code.key} \
#         --region ${var.aws_region} || true
#     EOT
#   }
#
#   depends_on = [
#     module.lambda_rule_executor,
#     module.lambda_api_gateway,
#     aws_s3_object.lambda_rule_executor_code,
#     aws_s3_object.lambda_api_gateway_code
#   ]
# }
