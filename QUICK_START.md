# Quick Start Guide

## Prerequisites Check

```bash
# Verify tools are installed
terraform --version    # Should be >= 1.5.0
terragrunt --version   # Should be >= 0.48.0
aws --version          # Should be >= 2.x
python --version       # Should be >= 3.9
node --version         # Should be >= 16.x
```

## 5-Minute Setup

### 1. Configure AWS

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and Region
```

### 2. Bootstrap Terraform Backend

```bash
./scripts/bootstrap.sh us-east-1
# Note the S3 bucket and DynamoDB table names
# Update terragrunt/terragrunt.hcl with these values
```

### 3. Configure Environment

```bash
# Edit environment configuration
vim terragrunt/envs/dev/terragrunt.hcl

# Key settings to review:
# - aws_region
# - vpc_cidr (or existing VPC ID)
# - database_instance_class
# - glue_worker_type
```

### 4. Deploy

```bash
# One-command deployment
./scripts/deploy.sh dev
```

This will:
- Build Lambda packages
- Build UI
- Deploy infrastructure (15-20 minutes)
- Run database migrations
- Deploy UI to S3

### 5. Get Access Information

```bash
cd terragrunt/envs/dev
terragrunt output

# Key outputs:
# - ui_url: Web UI URL
# - api_endpoint: API Gateway URL
# - db_endpoint: Database endpoint
```

### 6. Create Admin User (if using Cognito)

```bash
# Get User Pool ID
USER_POOL_ID=$(terragrunt output -raw cognito_user_pool_id)

# Create user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password TempPass123!
```

## Common Tasks

### View Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/rules-executor-dev --follow

# Glue job logs
aws logs tail /aws-glue/jobs/bulk-validator-dev --follow
```

### Update Lambda Code

```bash
# Rebuild and redeploy
./scripts/build_lambdas.sh
cd terragrunt/envs/dev
terragrunt apply
```

### Update UI

```bash
cd src/ui/frontend
npm run build
UI_BUCKET=$(cd ../../../terragrunt/envs/dev && terragrunt output -raw ui_bucket_name)
aws s3 sync build/ s3://$UI_BUCKET/
```

### Run Database Migration

```bash
./scripts/run_migrations.sh dev
```

### Seed Sample Data

```bash
python scripts/seed_metadata.py --env dev
```

## Troubleshooting

### Deployment Fails

1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify permissions: Ensure IAM user has required permissions
3. Check Terraform state: `cd terragrunt/envs/dev && terragrunt show`

### Database Connection Issues

1. Verify security groups allow Lambda → RDS traffic
2. Check Lambda is in VPC: `aws lambda get-function-configuration --function-name rules-executor-dev`
3. Verify database endpoint: `terragrunt output db_endpoint`

### UI Not Loading

1. Check S3 bucket: `aws s3 ls s3://$(terragrunt output -raw ui_bucket_name)`
2. Verify CloudFront distribution: `aws cloudfront get-distribution --id $(terragrunt output -raw cloudfront_distribution_id)`
3. Invalidate cache: `aws cloudfront create-invalidation --distribution-id $CF_ID --paths "/*"`

## Next Steps

1. **Configure Data Sources**: Add your data source connections via UI or API
2. **Create Rules**: Define validation rules in the UI
3. **Assign Rules**: Map rules to tables/columns
4. **Schedule Validations**: Configure EventBridge schedules
5. **Monitor**: Check CloudWatch dashboards for metrics

## Getting Help

- **Documentation**: See README.md, ARCHITECTURE.md, DEPLOYMENT.md
- **Project Summary**: See PROJECT_SUMMARY.md
- **Troubleshooting**: See DEPLOYMENT.md troubleshooting section
