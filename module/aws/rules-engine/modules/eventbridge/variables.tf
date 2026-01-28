variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "rule_executor_lambda_arn" {
  type = string
}

variable "rule_executor_lambda_name" {
  type = string
}

variable "schedule_expressions" {
  type    = map(string)
  default = {}
}

variable "tags" {
  type    = map(string)
  default = {}
}
