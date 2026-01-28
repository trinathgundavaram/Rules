variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "lambda_function_names" {
  type = list(string)
}

variable "glue_job_name" {
  type = string
}

variable "sns_topic_arn" {
  type    = string
  default = ""
}

variable "enable_alarms" {
  type    = bool
  default = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
