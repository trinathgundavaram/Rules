# Terragrunt Configuration

This directory contains Terragrunt configurations for deploying the Rules Engine Framework.

## Structure

```
terragrunt/
├── terragrunt.hcl          # Root configuration with remote state
└── envs/
    ├── common.hcl          # Common settings for all environments
    ├── dev/
    │   └── terragrunt.hcl  # Development environment
    └── prod/
        └── terragrunt.hcl  # Production environment
```

## Usage

### Single Module Deployment (Root Level)

Deploy everything from project root:

```bash
# From project root directory
terragrunt apply
```

### Environment-Specific Deployment

```bash
# Development
cd terragrunt/envs/dev
terragrunt apply

# Production
cd terragrunt/envs/prod
terragrunt apply
```

## Configuration

### Environment Variables

Set these before running Terragrunt:

```bash
export TF_STATE_BUCKET="your-terraform-state-bucket"
export TF_STATE_LOCK_TABLE="terraform-state-lock"
export AWS_REGION="us-east-1"
```

### Required Inputs

Edit the environment-specific `terragrunt.hcl` files to provide:

- `vpc_id` - VPC ID
- `database_subnet_ids` - Database subnet IDs (at least 2)
- `lambda_subnet_ids` - Lambda subnet IDs (if using VPC)

## Features

- ✅ **Automatic code packaging** - Lambda functions packaged automatically
- ✅ **Code deployment** - Glue scripts uploaded to S3 automatically
- ✅ **Remote state** - S3 backend configured automatically
- ✅ **State locking** - DynamoDB table for concurrent safety
- ✅ **Environment isolation** - Separate configs per environment
- ✅ **Common settings** - Shared configuration in `common.hcl`

## Quick Start

1. **Configure environment variables**
2. **Edit environment-specific terragrunt.hcl** with your VPC/subnet IDs
3. **Run**: `terragrunt apply`

That's it! Infrastructure and code will be deployed together.
