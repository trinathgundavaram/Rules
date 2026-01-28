# Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Data Rules Engine Framework to AWS using Terraform and Terragrunt.

## Prerequisites

### Required Tools

- **Terraform** >= 1.5.0
- **Terragrunt** >= 0.48.0
- **AWS CLI** >= 2.x
- **Python** >= 3.9
- **Node.js** >= 16.x (for UI)
- **Docker** (for local testing)

### AWS Account Setup

1. **Create AWS Account** or use existing
2. **Configure AWS CLI**:
   ```bash
   aws configure
   ```
3. **Verify Permissions**: Your IAM user/role needs:
   - AdministratorAccess (for initial setup)
   - Or specific permissions for: VPC, RDS, Lambda, Glue, S3, IAM, API Gateway, CloudFront, Secrets Manager, EventBridge, SNS, Cognito, CloudWatch

### Terraform Backend Setup

The framework uses S3 for Terraform state storage and DynamoDB for state locking.

#### Option 1: Automated Bootstrap

```bash
./scripts/bootstrap.sh
```

This script will:
- Create S3 bucket for Terraform state
- Create DynamoDB table for state locking
- Configure backend in `terragrunt/terragrunt.hcl`

#### Option 2: Manual Setup

```bash
# Create S3 bucket
aws s3 mb s3://your-terraform-state-bucket --region us-east-1
aws s3api put-bucket-versioning \
  --bucket your-terraform-state-bucket \
  --versioning-configuration Status=Enabled

# Create DynamoDB table
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## Deployment Steps

### Step 1: Configure Terragrunt Backend

Edit `terragrunt/terragrunt.hcl`:

```hcl
remote_state {
  backend = "s3"
  config = {
    bucket         = "your-terraform-state-bucket"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

### Step 2: Configure Environment

Edit `terragrunt/envs/dev/terragrunt.hcl`:

```hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../terraform"
}

inputs = {
  project_name = "rules-engine"
  environment  = "dev"
  aws_region   = "us-east-1"

  # VPC Configuration
  create_vpc              = true
  vpc_cidr                = "10.0.0.0/16"
  
  # Or use existing VPC
  # vpc_id                 = "vpc-xxxxxxxxx"
  # database_subnet_ids    = ["subnet-xxx", "subnet-yyy"]
  # lambda_subnet_ids      = ["subnet-xxx", "subnet-yyy"]

  # Database Configuration
  database_name           = "rules_engine_dev"
  database_username       = "rulesadmin"
  # database_password will be auto-generated if not provided
  database_instance_class = "db.t3.medium"
  database_instance_count = 2
  database_engine_version = "15.4"
  database_backup_retention = 7
  database_storage_encrypted = true

  # Lambda Configuration
  lambda_memory_size      = 512
  lambda_timeout          = 300

  # Glue Configuration
  glue_worker_type        = "G.1X"
  glue_number_of_workers  = 2
  glue_version            = "4.0"

  # S3 Configuration
  enable_s3_versioning    = true
  enable_s3_encryption    = true

  # API Gateway Configuration
  enable_api_cors         = true
  api_cors_origins        = ["*"]

  # EventBridge Schedules
  eventbridge_schedules = {
    daily_validation = "cron(0 2 * * ? *)"  # Daily at 2 AM UTC
  }

  # Monitoring
  enable_cloudwatch_alarms = true

  # Tags
  tags = {
    Environment = "dev"
    Project     = "DataRulesEngine"
    ManagedBy   = "Terraform"
    CostCenter  = "Engineering"
  }
}
```

### Step 3: Build Lambda Packages

```bash
./scripts/build_lambdas.sh
```

This script:
- Packages each Lambda function with dependencies
- Uploads to S3 code bucket (created by Terraform)
- Outputs package locations for Terraform

### Step 4: Deploy Infrastructure

```bash
cd terragrunt/envs/dev

# Review what will be created
terragrunt plan

# Apply infrastructure
terragrunt apply

# Confirm with 'yes' when prompted
```

**Expected Duration**: 15-20 minutes

**Resources Created**:
- VPC, Subnets, Security Groups
- Aurora PostgreSQL cluster
- S3 buckets (code, results, temp, UI)
- Lambda functions
- Glue jobs
- API Gateway
- CloudFront distribution
- EventBridge rules
- SNS topics
- Cognito User Pool
- CloudWatch dashboards and alarms
- IAM roles and policies

### Step 5: Initialize Database

```bash
# Get database endpoint
cd terragrunt/envs/dev
DB_ENDPOINT=$(terragrunt output -raw db_endpoint)
DB_SECRET_ARN=$(terragrunt output -raw db_secret_arn)

# Get database password from Secrets Manager
DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id $DB_SECRET_ARN \
  --query SecretString --output text | jq -r .password)

# Run schema
psql -h $DB_ENDPOINT -U rulesadmin -d rules_engine_dev \
  -f ../../../sql/metadata_schema.sql
```

Or use the migration script:

```bash
./scripts/run_migrations.sh dev
```

### Step 6: Seed Sample Data (Optional)

```bash
python scripts/seed_metadata.py --env dev
```

### Step 7: Deploy UI

```bash
# Build UI
cd src/ui/frontend
npm install
npm run build

# Get UI bucket name
cd ../../../terragrunt/envs/dev
UI_BUCKET=$(terragrunt output -raw ui_bucket_name)

# Upload to S3
cd ../../..
aws s3 sync src/ui/frontend/build/ s3://$UI_BUCKET/

# Invalidate CloudFront cache
CF_ID=$(cd terragrunt/envs/dev && terragrunt output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation \
  --distribution-id $CF_ID \
  --paths "/*"
```

### Step 8: Verify Deployment

```bash
cd terragrunt/envs/dev

# Get outputs
terragrunt output

# Test API endpoint
API_URL=$(terragrunt output -raw api_endpoint)
curl $API_URL/health

# Access UI
UI_URL=$(terragrunt output -raw ui_url)
echo "UI available at: $UI_URL"
```

## Post-Deployment Configuration

### 1. Configure Cognito Users

```bash
# Get Cognito User Pool ID
USER_POOL_ID=$(cd terragrunt/envs/dev && terragrunt output -raw cognito_user_pool_id)

# Create admin user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password TempPass123! \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username admin \
  --password YourSecurePassword123! \
  --permanent
```

### 2. Configure Data Sources

Via UI:
1. Navigate to "Data Sources"
2. Click "Add Data Source"
3. Enter connection details
4. Test connection
5. Save

Via API:
```bash
curl -X POST $API_URL/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "Production Database",
    "source_type": "sqlserver",
    "connection_config": {
      "host": "db.example.com",
      "port": 1433,
      "database": "production"
    }
  }'
```

### 3. Configure EventBridge Schedules

Edit `terragrunt/envs/dev/terragrunt.hcl` to modify schedules:

```hcl
eventbridge_schedules = {
  daily_validation    = "cron(0 2 * * ? *)"   # Daily at 2 AM
  hourly_validation   = "cron(0 * * * ? *)"   # Every hour
  weekly_report       = "cron(0 9 ? * MON *)"  # Monday at 9 AM
}
```

Then apply:
```bash
terragrunt apply
```

## Updating Deployment

### Update Infrastructure

```bash
cd terragrunt/envs/dev

# Make changes to terragrunt.hcl or terraform files
vim terragrunt.hcl

# Review changes
terragrunt plan

# Apply updates
terragrunt apply
```

### Update Lambda Functions

```bash
# Rebuild packages
./scripts/build_lambdas.sh

# Update Lambda code (Terraform will detect S3 changes)
cd terragrunt/envs/dev
terragrunt apply
```

### Update UI

```bash
cd src/ui/frontend
npm install  # If package.json changed
npm run build

# Deploy
UI_BUCKET=$(cd ../../../terragrunt/envs/dev && terragrunt output -raw ui_bucket_name)
aws s3 sync build/ s3://$UI_BUCKET/

# Invalidate CloudFront
CF_ID=$(cd terragrunt/envs/dev && terragrunt output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id $CF_ID --paths "/*"
```

### Update Database Schema

```bash
# Run new migrations
./scripts/run_migrations.sh dev

# Or manually
psql -h $DB_ENDPOINT -U rulesadmin -d rules_engine_dev \
  -f sql/migrations/YYYYMMDD_description.sql
```

## Multi-Environment Deployment

### Deploy to Test Environment

```bash
# Copy dev configuration
cp -r terragrunt/envs/dev terragrunt/envs/test

# Edit test configuration
vim terragrunt/envs/test/terragrunt.hcl
# Change: environment = "test", different VPC CIDR, etc.

# Deploy
cd terragrunt/envs/test
terragrunt apply
```

### Deploy to Production

```bash
# Copy test configuration
cp -r terragrunt/envs/test terragrunt/envs/prod

# Edit production configuration
vim terragrunt/envs/prod/terragrunt.hcl
# Change: environment = "prod", larger instances, etc.

# Deploy (with extra caution)
cd terragrunt/envs/prod
terragrunt plan  # Review carefully
terragrunt apply
```

## Destroying Deployment

### Destroy Specific Environment

```bash
cd terragrunt/envs/dev
terragrunt destroy

# Confirm with 'yes'
```

**Warning**: This will delete all resources including:
- Database (with data!)
- S3 buckets (with results!)
- All infrastructure

**Before Destroying**:
1. Backup database: `./scripts/backup_database.sh dev`
2. Export S3 data: `aws s3 sync s3://results-bucket ./backup/`
3. Export Terraform state: `terragrunt output -json > outputs.json`

### Destroy All Environments

```bash
./scripts/destroy.sh all
```

## Troubleshooting Deployment

### Terraform State Locked

```bash
# If deployment fails due to state lock
aws dynamodb delete-item \
  --table-name terraform-state-lock \
  --key '{"LockID": {"S": "your-lock-id"}}'
```

### Database Connection Issues

```bash
# Verify security groups
aws ec2 describe-security-groups \
  --filters "Name=tag:Name,Values=*rules-engine*"

# Check Lambda VPC configuration
aws lambda get-function-configuration \
  --function-name rules-executor-dev
```

### Lambda Deployment Failures

```bash
# Check Lambda logs
aws logs tail /aws/lambda/rules-executor-dev --follow

# Verify S3 package exists
aws s3 ls s3://rules-engine-code-dev/lambda-packages/
```

### CloudFront Not Updating

```bash
# Force invalidation
aws cloudfront create-invalidation \
  --distribution-id $CF_ID \
  --paths "/*" \
  --invalidation-batch '{"Paths": {"Quantity": 1, "Items": ["/*"]}, "CallerReference": "'$(date +%s)'"}'
```

## Deployment Checklist

### Pre-Deployment

- [ ] AWS account configured
- [ ] Terraform/Terragrunt installed
- [ ] Backend S3 bucket created
- [ ] Configuration files reviewed
- [ ] Lambda packages built
- [ ] Database credentials prepared

### Deployment

- [ ] Infrastructure deployed successfully
- [ ] Database initialized
- [ ] Lambda functions deployed
- [ ] Glue jobs created
- [ ] API Gateway configured
- [ ] CloudFront distribution created
- [ ] UI deployed to S3

### Post-Deployment

- [ ] Database migrations run
- [ ] Sample data seeded (optional)
- [ ] Cognito users created
- [ ] Data sources configured
- [ ] EventBridge schedules active
- [ ] CloudWatch alarms configured
- [ ] Health checks passing
- [ ] UI accessible
- [ ] API endpoints responding

### Verification

- [ ] Create test rule via UI
- [ ] Assign rule to test table
- [ ] Trigger validation manually
- [ ] Verify results in UI
- [ ] Check CloudWatch logs
- [ ] Verify SNS notifications (if configured)

## Cost Estimation

### Development Environment (Monthly)

- **RDS**: db.t3.medium (2 instances): ~$150
- **Lambda**: 1M invocations: ~$20
- **Glue**: 10 hours @ G.1X: ~$45
- **S3**: 100 GB storage: ~$2.30
- **API Gateway**: 1M requests: ~$3.50
- **CloudFront**: 10 GB transfer: ~$0.85
- **Other**: Data transfer, CloudWatch: ~$30

**Total**: ~$250/month

### Production Environment (Monthly)

- **RDS**: db.r6g.xlarge (2 instances): ~$800
- **Lambda**: 10M invocations: ~$200
- **Glue**: 100 hours @ G.2X: ~$900
- **S3**: 1 TB storage: ~$23
- **API Gateway**: 10M requests: ~$35
- **CloudFront**: 100 GB transfer: ~$8.50
- **Other**: ~$200

**Total**: ~$2,200/month

*Costs vary based on usage patterns and AWS pricing changes*

## Support

For deployment issues:
1. Check [Troubleshooting](#troubleshooting-deployment) section
2. Review CloudWatch logs
3. Check Terraform state: `terragrunt show`
4. Open GitHub issue with deployment logs
