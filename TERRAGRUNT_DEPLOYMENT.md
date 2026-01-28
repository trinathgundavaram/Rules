# Terragrunt Deployment Guide

## Overview

The Rules Engine Framework is now configured to deploy as a **single module** using Terragrunt. Running `terragrunt apply` at the module level will automatically:

1. ✅ Package Lambda functions
2. ✅ Upload Glue scripts to S3
3. ✅ Deploy all infrastructure
4. ✅ Deploy code artifacts

## Structure

```
.
├── terragrunt.hcl                    # Root terragrunt config (single module)
├── terragrunt/
│   ├── terragrunt.hcl               # Root configuration with remote state
│   └── envs/
│       ├── common.hcl               # Common settings
│       ├── dev/
│       │   └── terragrunt.hcl       # Dev environment
│       └── prod/
│           └── terragrunt.hcl       # Prod environment
└── terraform/
    ├── main.tf                      # Main infrastructure
    ├── code_deployment.tf            # Automatic code packaging & upload
    └── modules/                      # Reusable modules
```

## Quick Start

### Option 1: Single Module Deployment (Recommended)

Deploy everything from the root:

```bash
# From project root
terragrunt apply
```

This will:
- Package Lambda functions automatically
- Upload Glue scripts to S3
- Deploy all infrastructure
- Deploy code artifacts

### Option 2: Environment-Specific Deployment

```bash
# Development
cd terragrunt/envs/dev
terragrunt apply

# Production
cd terragrunt/envs/prod
terragrunt apply
```

## Prerequisites

1. **Terragrunt** installed ([Installation Guide](https://terragrunt.gruntwork.io/docs/getting-started/install/))
2. **Terraform** >= 1.0
3. **AWS CLI** configured
4. **S3 bucket** for Terraform state (optional but recommended)

## Configuration

### 1. Set Environment Variables

```bash
export TF_STATE_BUCKET="your-terraform-state-bucket"
export TF_STATE_LOCK_TABLE="terraform-state-lock"
export AWS_REGION="us-east-1"
```

### 2. Configure Variables

Edit `terragrunt.hcl` or environment-specific files:

```hcl
inputs = {
  vpc_id = "vpc-xxxxxxxxx"
  database_subnet_ids = ["subnet-xxx", "subnet-yyy"]
  lambda_subnet_ids = ["subnet-xxx", "subnet-yyy"]
}
```

### 3. Deploy

```bash
# Initialize (first time only)
terragrunt init

# Plan
terragrunt plan

# Apply
terragrunt apply
```

## Automatic Code Deployment

The Terraform configuration automatically handles:

### Lambda Functions

- **Packaging**: Lambda functions are automatically packaged using `archive_file`
- **Upload**: Packages are uploaded to S3 code bucket
- **Deployment**: Lambda functions are updated with new code on each apply

### Glue Scripts

- **Upload**: Glue scripts are automatically uploaded to S3
- **Dependencies**: Python source files are synced to S3 for Glue imports
- **Versioning**: Files are versioned by content hash

### Code Changes Detection

Terraform detects code changes through:
- File content hashes
- Archive file checksums
- S3 object etags

## Deployment Flow

```
terragrunt apply
    ↓
1. Generate provider configuration
    ↓
2. Package Lambda functions (archive_file)
    ↓
3. Upload Lambda packages to S3
    ↓
4. Upload Glue scripts to S3
    ↓
5. Sync Python dependencies for Glue
    ↓
6. Deploy infrastructure (RDS, Lambda, API Gateway, etc.)
    ↓
7. Update Lambda functions with new code
    ↓
8. Initialize database schema (manual step)
```

## Key Features

### ✅ Single Command Deployment

```bash
terragrunt apply  # Deploys everything!
```

### ✅ Automatic Code Packaging

No need to manually run packaging scripts - Terraform handles it.

### ✅ Code Versioning

- Lambda packages: Versioned by MD5 hash
- Glue scripts: Versioned by content hash
- S3 objects: Tagged with metadata

### ✅ Environment Management

- Common settings in `envs/common.hcl`
- Environment-specific overrides
- Remote state per environment

### ✅ State Management

- Remote state in S3
- State locking with DynamoDB
- Automatic backend generation

## Environment Configuration

### Development (`terragrunt/envs/dev/terragrunt.hcl`)

```hcl
inputs = {
  environment = "dev"
  database_instance_class = "db.t4g.medium"
  database_instance_count = 1
  glue_number_of_workers = 1
}
```

### Production (`terragrunt/envs/prod/terragrunt.hcl`)

```hcl
inputs = {
  environment = "prod"
  database_instance_class = "db.r6g.xlarge"
  database_instance_count = 2
  glue_number_of_workers = 10
}
```

## Post-Deployment

After `terragrunt apply` completes:

### 1. Initialize Database Schema

```bash
# Get database endpoint
terragrunt output database_endpoint

# Run schema
psql -h <endpoint> -U rulesadmin -d rules_engine \
  -f ../sql/metadata_schema.sql
```

### 2. Test API

```bash
# Get API URL
terragrunt output api_gateway_url

# Test
curl $(terragrunt output -raw api_gateway_url)/health
```

## Updating Code

When you update Lambda or Glue code:

```bash
# Just run apply - code will be automatically packaged and deployed
terragrunt apply
```

Terraform will detect changes and:
1. Re-package Lambda functions
2. Upload new versions to S3
3. Update Lambda functions
4. Update Glue job script path

## Troubleshooting

### Code Not Updating

If Lambda code isn't updating, check:
1. Source files changed
2. Archive file hash changed
3. Lambda function source_code_hash updated

### Glue Script Not Found

Ensure:
1. S3 bucket exists
2. Glue script uploaded successfully
3. IAM role has S3 read permissions

### State Lock Issues

If state is locked:
```bash
# Check lock table
aws dynamodb describe-table --table-name terraform-state-lock

# Force unlock (use with caution)
terragrunt force-unlock <lock-id>
```

## Advanced Usage

### Using S3 for Large Lambda Packages

For Lambda packages > 50MB:

```hcl
inputs = {
  use_s3_for_lambda_code = true
}
```

This will:
- Upload packages to S3
- Use S3 source for Lambda deployment
- Enable versioning

### Custom Code Paths

Override source paths:

```hcl
locals {
  lambda_source_root = "/custom/path/to/lambda"
  glue_source_root   = "/custom/path/to/glue"
}
```

## Comparison: Terraform vs Terragrunt

| Feature | Terraform | Terragrunt |
|---------|-----------|------------|
| Code Packaging | Manual script | Automatic |
| State Management | Manual config | Auto-generated |
| Environment Management | Workspaces | Directory structure |
| Code Deployment | Separate step | Integrated |
| Single Command | No | Yes |

## Best Practices

1. ✅ **Use remote state** - Configure S3 backend
2. ✅ **Environment isolation** - Separate directories
3. ✅ **Common settings** - Use `common.hcl`
4. ✅ **Version control** - Commit terragrunt configs
5. ✅ **Code changes** - Let Terraform detect automatically
6. ✅ **State locking** - Use DynamoDB table

## Migration from Terraform

If you were using Terraform directly:

1. **Keep Terraform code** - No changes needed
2. **Add Terragrunt config** - Create `terragrunt.hcl`
3. **Migrate state** - Use `terragrunt init -migrate-state`
4. **Update workflows** - Use `terragrunt` commands

## Support

For issues:
1. Check Terragrunt logs: `terragrunt apply --terragrunt-log-level debug`
2. Check Terraform plan: `terragrunt plan`
3. Verify code packaging: Check `lambda_packages/` directory
4. Check S3 uploads: Verify objects in code bucket

## Next Steps

1. ✅ Configure `terragrunt.hcl` with your values
2. ✅ Set up S3 backend (optional)
3. ✅ Run `terragrunt init`
4. ✅ Run `terragrunt plan`
5. ✅ Run `terragrunt apply`
6. ✅ Initialize database schema
7. ✅ Test API endpoint

The entire infrastructure and code will be deployed with a single command! 🚀
