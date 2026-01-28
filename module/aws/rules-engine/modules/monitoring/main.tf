# CloudWatch Monitoring Module

# SNS Topic for Alerts (if not provided)
resource "aws_sns_topic" "alerts" {
  count = var.sns_topic_arn == "" ? 1 : 0
  name  = "${var.project_name}-alerts-${var.environment}"

  tags = var.tags
}

locals {
  sns_topic_arn = var.sns_topic_arn != "" ? var.sns_topic_arn : aws_sns_topic.alerts[0].arn
}

# Lambda Error Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = var.enable_alarms ? toset(var.lambda_function_names) : []

  alarm_name          = "${each.value}-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period               = 300
  statistic            = "Sum"
  threshold            = 5
  alarm_description    = "This metric monitors lambda errors"
  alarm_actions        = [local.sns_topic_arn]

  dimensions = {
    FunctionName = each.value
  }

  tags = var.tags
}

# Lambda Duration Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  for_each = var.enable_alarms ? toset(var.lambda_function_names) : []

  alarm_name          = "${each.value}-duration-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period               = 300
  statistic            = "Average"
  threshold            = 300000  # 5 minutes in milliseconds
  alarm_description    = "This metric monitors lambda duration"
  alarm_actions        = [local.sns_topic_arn]

  dimensions = {
    FunctionName = each.value
  }

  tags = var.tags
}

# Glue Job Failure Alarms
resource "aws_cloudwatch_metric_alarm" "glue_failures" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.glue_job_name}-failures-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "glue.driver.ExecutorAllocationManager.executor.numberAllocatedExecutors"
  namespace           = "Glue"
  period               = 300
  statistic            = "Sum"
  threshold            = 0
  alarm_description    = "This metric monitors Glue job failures"
  alarm_actions        = [local.sns_topic_arn]

  dimensions = {
    JobName = var.glue_job_name
  }

  tags = var.tags
}

# Custom Metrics Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  count = var.enable_alarms ? 1 : 0

  dashboard_name = "${var.project_name}-dashboard-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            for func_name in var.lambda_function_names : [
              "AWS/Lambda",
              "Invocations",
              "FunctionName",
              func_name
            ]
          ]
          period = 300
          stat   = "Sum"
          region = "us-east-1"
          title  = "Lambda Invocations"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            for func_name in var.lambda_function_names : [
              "AWS/Lambda",
              "Errors",
              "FunctionName",
              func_name
            ]
          ]
          period = 300
          stat   = "Sum"
          region = "us-east-1"
          title  = "Lambda Errors"
        }
      }
    ]
  })
}
