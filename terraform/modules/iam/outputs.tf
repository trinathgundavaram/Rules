output "lambda_execution_role_arn" {
  value = aws_iam_role.lambda_execution.arn
}

output "lambda_security_group_id" {
  value = length(aws_security_group.lambda) > 0 ? aws_security_group.lambda[0].id : null
}

output "glue_role_arn" {
  value = aws_iam_role.glue.arn
}
