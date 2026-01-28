# EventBridge Rules Module

resource "aws_cloudwatch_event_rule" "schedules" {
  for_each = var.schedule_expressions

  name                = "${var.project_name}-schedule-${each.key}-${var.environment}"
  description         = "Schedule for ${each.key}"
  schedule_expression = each.value

  tags = merge(var.tags, {
    Name = "${var.project_name}-schedule-${each.key}-${var.environment}"
  })
}

resource "aws_cloudwatch_event_target" "lambda" {
  for_each = aws_cloudwatch_event_rule.schedules

  rule      = each.value.name
  target_id = "${var.project_name}-target-${each.key}-${var.environment}"
  arn       = var.rule_executor_lambda_arn
}

resource "aws_lambda_permission" "eventbridge" {
  for_each = aws_cloudwatch_event_rule.schedules

  statement_id  = "AllowExecutionFromEventBridge-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = var.rule_executor_lambda_name
  principal     = "events.amazonaws.com"
  source_arn    = each.value.arn
}
