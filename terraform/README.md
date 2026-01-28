# Rules Engine Framework - Terraform Deployment

This directory contains Terraform configurations to deploy the Rules Engine Framework to AWS.

## Prerequisites

1. **Terraform** >= 1.0 installed ([Download](https://www.terraform.io/downloads))
2. **AWS CLI** configured with appropriate credentials
3. **AWS Account** with permissions to create:
   - RDS (Aurora PostgreSQL)
   - Lambda functions
   - API Gateway
   - Glue jobs
   - S3 buckets
   - IAM roles and policies
   - CloudWatch logs and alarms
   - Secrets Manager
   - EventBridge rules

## Quick Start

### 1. Configure Variables

Copy the example variables file and customize:

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 2. Initialize Terraform

```bash
cd terraform
chmod +x deploy.sh
./deploy.sh init
```

### 3. Review Plan

```bash
./deploy.sh plan
```

### 4. Deploy

```bash
./deploy.sh apply
```

## Module Structure

```
terraform/
├── main.tf                 # Main configuration
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── terraform.tfvars.example # Example variables
├── deploy.sh               # Deployment script
└── modules/
    ├── database/           # Aurora PostgreSQL module
    ├── lambda/             # Lambda function module
    ├── s3/                 # S3 buckets module
    ├── iam/                # IAM roles and policies
    ├── api_gateway/        # API Gateway module
    ├── glue/               # Glue job module
    ├── secrets/            # Secrets Manager module
    ├── eventbridge/         # EventBridge rules
    └── monitoring/          # CloudWatch monitoring
```

## Required Variables

### Minimum Required Variables

You must provide these variables (either in `terraform.tfvars` or via command line):

- `vpc_id` - VPC ID for resources
- `database_subnet_ids` - Subnet IDs for Aurora PostgreSQL (at least 2 in different AZs)

### Optional Variables

All other variables have defaults but can be customized. See `variables.tf` for details.

## Deployment Steps

### Step 1: Prepare Lambda Code

Before deploying, package the Lambda functions:

```bash
# Package rule executor
cd ../src/lambda/rule_executor
zip -r ../../../terraform/lambda_packages/rule_executor.zip .

# Package API Gateway
cd ../api_gateway
zip -r ../../../terraform/lambda_packages/api_gateway.zip .
```

Or use the provided script:

```bash
./scripts/package_lambdas.sh
```

### Step 2: Upload Glue Scripts

Upload Glue scripts to S3 (will be done automatically if code bucket exists):

```bash
aws s3 cp ../src/glue/bulk_validator.py s3://<code-bucket>/glue/bulk_validator.py
```

### Step 3: Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply
```

## Post-Deployment

### 1. Initialize Database Schema

After deployment, initialize the database schema:

```bash
# Get database endpoint from outputs
terraform output database_endpoint

# Run schema SQL
psql -h <endpoint> -U <username> -d <database> -f ../sql/metadata_schema.sql
```

### 2. Configure Secrets

Database credentials are stored in AWS Secrets Manager. Access them:

```bash
aws secretsmanager get-secret-value \
  --secret-id rules-engine-db-credentials-dev \
  --query SecretString --output text | jq .
```

### 3. Test API

Get the API Gateway URL:

```bash
terraform output api_gateway_url
```

Test the API:

```bash
curl https://<api-id>.execute-api.us-east-1.amazonaws.com/health
```

## Outputs

After deployment, view outputs:

```bash
terraform output
```

Key outputs:
- `database_endpoint` - Aurora PostgreSQL endpoint
- `api_gateway_url` - API Gateway endpoint URL
- `lambda_rule_executor_arn` - Rule executor Lambda ARN
- `s3_results_bucket` - Results bucket name
- `glue_job_name` - Glue job name

## Environment-Specific Deployments

### Development

```bash
terraform workspace select dev
terraform apply -var-file=dev.tfvars
```

### Production

```bash
terraform workspace select prod
terraform apply -var-file=prod.tfvars
```

## Cost Estimation

Approximate monthly costs (us-east-1):

- **Aurora PostgreSQL** (db.r6g.large, 2 instances): ~$300-400
- **Lambda** (moderate usage): ~$10-50
- **API Gateway** (moderate usage): ~$5-20
- **Glue** (on-demand): ~$0.44/hour per DPU
- **S3** (storage + requests): ~$5-20
- **CloudWatch**: ~$5-10

**Total**: ~$325-500/month (varies by usage)

## Troubleshooting

### Common Issues

1. **Database subnet group error**
   - Ensure subnet IDs are in different availability zones
   - Ensure subnets have proper tags

2. **Lambda timeout**
   - Increase timeout in Lambda module
   - Check VPC configuration if Lambda needs database access

3. **Permission errors**
   - Verify IAM roles have correct policies
   - Check CloudWatch logs for detailed errors

4. **API Gateway 502 errors**
   - Check Lambda function logs
   - Verify Lambda permissions for API Gateway

### Viewing Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/rules-engine-rule-executor-dev --follow

# API Gateway logs
aws logs tail /aws/apigateway/rules-engine-dev --follow

# Glue logs
aws logs tail /aws-glue/jobs/rules-engine-bulk-validator-dev --follow
```

## Destroying Resources

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all resources including the database. Ensure you have backups!

## State Management

### Remote State (Recommended)

Configure S3 backend in `main.tf`:

```hcl
backend "s3" {
  bucket         = "your-terraform-state-bucket"
  key            = "rules-engine/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-state-lock"
}
```

### State Locking

Use DynamoDB for state locking to prevent concurrent modifications.

## Security Best Practices

1. **Never commit** `terraform.tfvars` with sensitive data
2. **Use Secrets Manager** for database credentials
3. **Enable encryption** for S3 buckets and RDS
4. **Use VPC** for Lambda functions accessing database
5. **Enable CloudWatch** logging and monitoring
6. **Restrict IAM** roles to minimum required permissions
7. **Use Terraform workspaces** for environment isolation

## Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Aurora PostgreSQL Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.AuroraPostgreSQL.html)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review Terraform plan output
3. Verify AWS service quotas
4. Check IAM permissions
