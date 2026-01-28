# Lambda Function Module

resource "aws_lambda_function" "main" {
  filename         = var.output_path
  function_name    = var.function_name
  role            = var.iam_role_arn
  handler         = var.handler
  source_code_hash = var.source_code_hash != null ? var.source_code_hash : filebase64sha256(var.output_path)
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
