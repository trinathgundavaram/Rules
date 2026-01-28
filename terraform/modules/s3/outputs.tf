output "results_bucket_name" {
  value = aws_s3_bucket.results.id
}

output "results_bucket_arn" {
  value = aws_s3_bucket.results.arn
}

output "temp_bucket_name" {
  value = aws_s3_bucket.temp.id
}

output "temp_bucket_arn" {
  value = aws_s3_bucket.temp.arn
}

output "code_bucket_name" {
  value = aws_s3_bucket.code.id
}

output "code_bucket_arn" {
  value = aws_s3_bucket.code.arn
}
