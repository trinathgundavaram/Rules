# Terraform Deployment Guide - Rules Engine Framework

## ✅ Terraform Infrastructure Created!

A complete Terraform module structure has been created to deploy the Rules Engine Framework to AWS.

## 📁 Structure Created

```
terraform/
├── main.tf                      # Main configuration orchestrating all modules
├── variables.tf                  # Input variables
├── outputs.tf                   # Output values
├── terraform.tfvars.example     # Example variables file
├── deploy.sh                    # Deployment script
├── README.md                    # Detailed deployment guide
├── .terraformignore            # Terraform ignore patterns
└── modules/
    ├── database/               # Aurora PostgreSQL module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── lambda/                 # Lambda function module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── s3/                     # S3 buckets module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── iam/                    # IAM roles and policies
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── api_gateway/            # API Gateway module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── glue/                   # Glue job module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── secrets/                # Secrets Manager module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── eventbridge/            # EventBridge rules
    │   ├── main.tf
    │   └── variables.tf
    └── monitoring/             # CloudWatch monitoring
        ├── main.tf
        └── variables.tf
```

**Total**: 28 Terraform files created

## 🏗️ Infrastructure Components

### 1. **Aurora PostgreSQL Database**
- Multi-AZ cluster configuration
- Automated backups
- Encryption at rest
- Enhanced monitoring
- Security groups

### 2. **Lambda Functions**
- **rule_executor**: Orchestrates validation execution
- **api_gateway**: REST API backend
- VPC configuration support
- CloudWatch logging
- IAM roles with least privilege

### 3. **API Gateway**
- HTTP API (v2)
- CORS configuration
- Lambda integration
- Access logging

### 4. **AWS Glue Jobs**
- Bulk validation job
- Configurable workers
- S3 integration
- CloudWatch logging

### 5. **S3 Buckets**
- Results bucket (90-day retention)
- Temp bucket (7-day retention)
- Code bucket (for Glue scripts)
- Versioning and encryption

### 6. **IAM Roles & Policies**
- Lambda execution role
- Glue execution role
- S3 access policies
- Secrets Manager access
- VPC access (if enabled)

### 7. **Secrets Manager**
- Database credentials storage
- Automatic rotation support

### 8. **EventBridge**
- Scheduled rule execution
- Configurable cron expressions

### 9. **CloudWatch**
- Log groups for all services
- Alarms for errors and duration
- Custom dashboard
- SNS notifications

## 🚀 Quick Start

### 1. Configure Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 2. Initialize Terraform

```bash
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

## 📋 Required Variables

Minimum required variables:

```hcl
vpc_id = "vpc-xxxxxxxxx"
database_subnet_ids = ["subnet-xxx", "subnet-yyy"]
```

All other variables have sensible defaults.

## 🔧 Deployment Steps

### Step 1: Package Lambda Functions

```bash
./scripts/package_lambdas.sh
```

This creates:
- `terraform/lambda_packages/rule_executor.zip`
- `terraform/lambda_packages/api_gateway.zip`

### Step 2: Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply
```

### Step 3: Initialize Database

After deployment, run the database schema:

```bash
# Get endpoint from outputs
terraform output database_endpoint

# Run schema
psql -h <endpoint> -U <username> -d rules_engine \
  -f ../sql/metadata_schema.sql
```

## 📊 Outputs

After deployment, view outputs:

```bash
terraform output
```

Key outputs:
- `database_endpoint` - Database connection endpoint
- `api_gateway_url` - API endpoint URL
- `s3_results_bucket` - Results bucket name
- `glue_job_name` - Glue job name
- `lambda_rule_executor_arn` - Lambda ARN

## 💰 Cost Estimation

Approximate monthly costs (us-east-1):

| Service | Cost |
|---------|------|
| Aurora PostgreSQL (2x db.r6g.large) | $300-400 |
| Lambda (moderate usage) | $10-50 |
| API Gateway | $5-20 |
| Glue (on-demand) | Variable |
| S3 Storage | $5-20 |
| CloudWatch | $5-10 |
| **Total** | **~$325-500/month** |

## 🔒 Security Features

✅ **Encryption**
- S3 buckets encrypted
- RDS encrypted at rest
- Secrets Manager encryption

✅ **Network Security**
- VPC isolation
- Security groups
- Private subnets

✅ **Access Control**
- IAM roles with least privilege
- Secrets Manager for credentials
- No hardcoded passwords

✅ **Monitoring**
- CloudWatch logs
- Alarms for errors
- SNS notifications

## 🛠️ Module Details

### Database Module
- Aurora PostgreSQL cluster
- Multi-AZ support
- Automated backups
- Enhanced monitoring

### Lambda Module
- Function deployment
- Environment variables
- VPC configuration
- CloudWatch logging

### S3 Module
- Three buckets (results, temp, code)
- Lifecycle policies
- Versioning
- Encryption

### IAM Module
- Lambda execution role
- Glue execution role
- Security groups
- Policy attachments

### API Gateway Module
- HTTP API v2
- Lambda integration
- CORS support
- Access logging

### Glue Module
- Job definition
- Worker configuration
- S3 integration
- CloudWatch logging

### Secrets Module
- Database credentials
- JSON format
- Automatic rotation ready

### EventBridge Module
- Scheduled rules
- Lambda targets
- Configurable schedules

### Monitoring Module
- CloudWatch alarms
- Custom dashboard
- SNS integration

## 📝 Customization

### Environment-Specific Deployments

Use Terraform workspaces:

```bash
# Development
terraform workspace new dev
terraform apply -var-file=dev.tfvars

# Production
terraform workspace new prod
terraform apply -var-file=prod.tfvars
```

### Adjusting Resources

Edit `terraform/main.tf` to:
- Change instance sizes
- Adjust Lambda memory/timeout
- Modify Glue worker configuration
- Update retention policies

## 🔍 Troubleshooting

### Common Issues

1. **Subnet errors**: Ensure subnets are in different AZs
2. **Permission errors**: Check IAM roles and policies
3. **Lambda timeouts**: Increase timeout or check VPC config
4. **Database connection**: Verify security groups allow access

### Viewing Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/rules-engine-rule-executor-dev --follow

# API Gateway logs
aws logs tail /aws/apigateway/rules-engine-dev --follow

# Glue logs
aws logs tail /aws-glue/jobs/rules-engine-bulk-validator-dev --follow
```

## 🗑️ Destroying Resources

```bash
terraform destroy
```

**Warning**: This deletes everything including the database!

## 📚 Additional Resources

- **Terraform Docs**: See `terraform/README.md`
- **AWS Provider**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **Architecture**: See `docs/architecture.md`

## ✅ Next Steps

1. ✅ Review `terraform/terraform.tfvars.example`
2. ✅ Configure your variables
3. ✅ Package Lambda functions
4. ✅ Deploy infrastructure
5. ✅ Initialize database schema
6. ✅ Test API endpoint
7. ✅ Configure EventBridge schedules

The Terraform module is production-ready and follows AWS best practices!
