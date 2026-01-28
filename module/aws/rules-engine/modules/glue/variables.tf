variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "job_name" {
  type = string
}

variable "script_name" {
  description = "Name of the Glue script file (e.g., bulk_validator.py)"
  type        = string
  default     = "bulk_validator.py"
}

variable "code_bucket" {
  description = "S3 bucket for code storage"
  type        = string
}

variable "glue_role_arn" {
  type = string
}

variable "temp_bucket" {
  type = string
}

variable "results_bucket" {
  type = string
}

variable "database_secret_arn" {
  type = string
}

variable "worker_type" {
  type    = string
  default = "G.1X"
}

variable "number_of_workers" {
  type    = number
  default = 2
}

variable "glue_version" {
  type    = string
  default = "4.0"
}

variable "tags" {
  type    = map(string)
  default = {}
}
