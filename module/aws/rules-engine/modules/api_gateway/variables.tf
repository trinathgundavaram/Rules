variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "lambda_function_arn" {
  type = string
}

variable "lambda_function_name" {
  type = string
}

variable "enable_cors" {
  type    = bool
  default = true
}

variable "cors_origins" {
  type    = list(string)
  default = ["*"]
}

variable "tags" {
  type    = map(string)
  default = {}
}
