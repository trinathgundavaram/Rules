#!/bin/bash
set -e

# Bootstrap script for Terraform backend setup
# Creates S3 bucket for state and DynamoDB table for locking

REGION=${1:-us-east-1}
STATE_BUCKET=${2:-rules-engine-terraform-state-$(date +%s)}
LOCK_TABLE=${3:-terraform-state-lock}

echo "Bootstrapping Terraform backend..."
echo "Region: $REGION"
echo "State Bucket: $STATE_BUCKET"
echo "Lock Table: $LOCK_TABLE"

# Create S3 bucket for Terraform state
echo "Creating S3 bucket for Terraform state..."
if aws s3 ls "s3://$STATE_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
    aws s3 mb "s3://$STATE_BUCKET" --region "$REGION"
    echo "Created S3 bucket: $STATE_BUCKET"
else
    echo "S3 bucket already exists: $STATE_BUCKET"
fi

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket "$STATE_BUCKET" \
    --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket "$STATE_BUCKET" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

# Create DynamoDB table for state locking
echo "Creating DynamoDB table for state locking..."
if aws dynamodb describe-table --table-name "$LOCK_TABLE" --region "$REGION" 2>&1 | grep -q 'ResourceNotFoundException'; then
    aws dynamodb create-table \
        --table-name "$LOCK_TABLE" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
    
    echo "Waiting for table to be active..."
    aws dynamodb wait table-exists --table-name "$LOCK_TABLE" --region "$REGION"
    echo "Created DynamoDB table: $LOCK_TABLE"
else
    echo "DynamoDB table already exists: $LOCK_TABLE"
fi

# Update terragrunt.hcl with backend configuration
echo ""
echo "Backend configuration:"
echo "  bucket         = \"$STATE_BUCKET\""
echo "  key            = \"\${path_relative_to_include()}/terraform.tfstate\""
echo "  region         = \"$REGION\""
echo "  encrypt        = true"
echo "  dynamodb_table = \"$LOCK_TABLE\""
echo ""
echo "Update terragrunt/terragrunt.hcl with the above configuration."
