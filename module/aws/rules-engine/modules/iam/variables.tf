variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "account_id" {
  type = string
}

variable "results_bucket_arn" {
  type = string
}

variable "temp_bucket_arn" {
  type = string
}

variable "code_bucket_arn" {
  type = string
}

variable "database_secret_arn" {
  type = string
}

variable "enable_lambda_vpc" {
  type    = bool
  default = false
}

variable "vpc_id" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
