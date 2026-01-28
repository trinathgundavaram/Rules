output "endpoint" {
  description = "RDS cluster endpoint"
  value       = aws_rds_cluster.main.endpoint
}

output "reader_endpoint" {
  description = "RDS cluster reader endpoint"
  value       = aws_rds_cluster.main.reader_endpoint
}

output "port" {
  description = "RDS cluster port"
  value       = aws_rds_cluster.main.port
}

output "cluster_id" {
  description = "RDS cluster identifier"
  value       = aws_rds_cluster.main.cluster_identifier
}

output "security_group_id" {
  description = "Security group ID"
  value       = length(aws_security_group.rds) > 0 ? aws_security_group.rds[0].id : null
}
