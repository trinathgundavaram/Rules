# S3 Buckets Module

resource "aws_s3_bucket" "results" {
  bucket = var.results_bucket_name

  tags = merge(var.tags, {
    Name        = var.results_bucket_name
    Purpose     = "Validation Results"
  })
}

resource "aws_s3_bucket_versioning" "results" {
  count  = var.enable_versioning ? 1 : 0
  bucket = aws_s3_bucket.results.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "results" {
  count  = var.enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.results.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "results" {
  bucket = aws_s3_bucket.results.id

  rule {
    id     = "delete_old_results"
    status = "Enabled"

    expiration {
      days = 90
    }
  }
}

resource "aws_s3_bucket" "temp" {
  bucket = var.temp_bucket_name

  tags = merge(var.tags, {
    Name        = var.temp_bucket_name
    Purpose     = "Temporary Files"
  })
}

resource "aws_s3_bucket_versioning" "temp" {
  count  = var.enable_versioning ? 1 : 0
  bucket = aws_s3_bucket.temp.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "temp" {
  count  = var.enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.temp.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "temp" {
  bucket = aws_s3_bucket.temp.id

  rule {
    id     = "delete_old_temp_files"
    status = "Enabled"

    expiration {
      days = 7
    }
  }
}

resource "aws_s3_bucket" "code" {
  bucket = var.code_bucket_name

  tags = merge(var.tags, {
    Name        = var.code_bucket_name
    Purpose     = "Code Artifacts"
  })
}

resource "aws_s3_bucket_versioning" "code" {
  count  = var.enable_versioning ? 1 : 0
  bucket = aws_s3_bucket.code.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "code" {
  count  = var.enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.code.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
