variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "results_bucket_name" {
  type = string
}

variable "temp_bucket_name" {
  type = string
}

variable "code_bucket_name" {
  type = string
}

variable "enable_versioning" {
  type    = bool
  default = true
}

variable "enable_encryption" {
  type    = bool
  default = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
