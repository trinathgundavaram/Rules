# Deployment Guide

## Overview

This project uses **Terragrunt** for infrastructure deployment and **GitHub Actions** with a reusable workflow for CI/CD automation. The infrastructure is organized as a module under `module/aws/rules-engine/`, with scripts co-located with their respective infrastructure components.

## Prerequisites

- AWS Account with appropriate permissions
- GitHub repository with Actions enabled
- Self-hosted runner: `MA-Analytics-Runner` (configured in workflow)
- GitHub Secrets configured (see below)
- Environment variable files (`.env.*`) configured

## Project Structure

### Script Organization

Scripts are organized within the module structure:

```
module/aws/rules-engine/
├── shared/                    # Shared Python libraries
│   ├── connectors/            # Data source connectors
│   ├── rules/                 # Rules engine core
│   ├── metadata/              # Database models & repository
│   └── utils/                 # Utilities
├── modules/
│   ├── glue/
│   │   └── scripts/           # Glue job scripts
│   │       └── bulk_validator.py
│   └── lambda/
│       └── scripts/           # Lambda function code
│           ├── rule_executor/
│           └── api_gateway/
```

**Key Benefits:**
- Scripts deploy automatically with infrastructure
- Terraform handles packaging and deployment
- No separate packaging scripts needed
- Shared libraries automatically included

## GitHub Actions Setup

### 1. Configure GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions, and add:

- `ORG_REPO_READ_ACCESS`: Token for accessing private repositories
- `TF_VAR_TDV_PASSWORD_DEV`: Database password for dev environment (if needed)
- `TF_VAR_TDV_PASSWORD_TEST`: Database password for test environment (if needed)
- `TF_VAR_TDV_PASSWORD_PROD`: Database password for prod environment (if needed)
- `ETL_OSS_TDV_PROD`: Production ETL OSS token (if needed)

### 2. Configure Environment Variables

Create `.env` files in the repository root:

**`.env.common`**:
```bash
TF_VERSION=1.5.0
TG_VERSION=0.48.0
```

**`.env.dev`**:
```bash
REGION=us-east-1
ACCOUNT_NUMBER=123456789012
VPC_ID=vpc-xxxxxxxxx
DATABASE_SUBNET_IDS=subnet-xxx,subnet-yyy
LAMBDA_SUBNET_IDS=subnet-xxx,subnet-yyy
```

**`.env.test`** and **`.env.prod`**: Similar structure with appropriate values

### 3. Configure GitHub Environments

Set up environments in GitHub (Settings → Environments):
- `dev`
- `test`
- `prod`

Each environment can have its own secrets and protection rules.

## Deployment Methods

### Method 1: GitHub Actions (Recommended)

#### Automatic CI

- **Push to `main` or `develop`**: Automatically runs CI checks (linting, tests, validation)
- **Pull Request**: Runs CI checks only

#### Manual Deployment

1. Go to **Actions** tab in GitHub
2. Select **"Deploy Rules Engine"** workflow
3. Click **"Run workflow"**
4. Select:
   - **Environment**: `dev`, `test`, or `prod`
   - **Action**: `plan`, `apply`, or `destroy`
5. Click **"Run workflow"**

The workflow will:
1. Checkout code
2. Set up GitHub read access token
3. Load environment variables from `.env` files
4. Authenticate to AWS via OIDC
5. Run Terragrunt action (plan/apply/destroy)
   - Terraform automatically packages Lambda functions
   - Terraform automatically uploads Glue scripts to S3

### Method 2: Local Terragrunt

#### Prerequisites

```bash
# Install Terragrunt
brew install terragrunt  # macOS
# or download from https://terragrunt.gruntwork.io/docs/getting-started/install/
```

#### Deploy Locally

```bash
cd module/aws/rules-engine

# Initialize
terragrunt init

# Plan
terragrunt plan

# Apply (Terraform will automatically package and deploy scripts)
terragrunt apply

# Destroy
terragrunt destroy
```

## How Scripts Are Deployed

### Glue Scripts

1. **Location**: `module/aws/rules-engine/modules/glue/scripts/`
2. **Deployment**: Terraform automatically:
   - Uploads all Python files from `scripts/` to S3 (`s3://code-bucket/glue/scripts/`)
   - Uploads shared libraries to S3 (`s3://code-bucket/glue/shared/`)
   - Configures Glue job to use the script from S3
   - Sets `--extra-py-files` to include shared libraries

### Lambda Functions

1. **Location**: `module/aws/rules-engine/modules/lambda/scripts/`
2. **Deployment**: Terraform automatically:
   - Copies Lambda code from `scripts/{lambda_name}/`
   - Copies shared libraries from `../../shared/`
   - Creates ZIP package
   - Deploys to Lambda

### Shared Libraries

1. **Location**: `module/aws/rules-engine/shared/`
2. **Usage**: Automatically included in:
   - Lambda function packages
   - Glue job extra Python files

## Post-Deployment Steps

### 1. Initialize Database

```bash
# Get database endpoint from Terraform outputs
cd module/aws/rules-engine
DB_ENDPOINT=$(terragrunt output -raw db_endpoint)
DB_SECRET_ARN=$(terragrunt output -raw db_secret_arn)

# Get password from Secrets Manager
DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id $DB_SECRET_ARN \
  --query SecretString --output text | jq -r .password)

# Run schema
psql -h $DB_ENDPOINT -U rulesadmin -d rules_engine_dev \
  -f ../../../sql/metadata_schema.sql
```

### 2. Verify Deployment

```bash
cd module/aws/rules-engine
terragrunt output

# Test API endpoint
API_URL=$(terragrunt output -raw api_endpoint)
curl $API_URL/health
```

## Environment-Specific Configuration

### Development

- Instance sizes: Smaller (db.t3.medium)
- Workers: Fewer (2 Glue workers)
- CORS: Permissive (*)
- Backup retention: 7 days

### Production

- Instance sizes: Larger (db.r6g.xlarge)
- Workers: More (10 Glue workers)
- CORS: Restricted to specific domains
- Backup retention: 30 days

Configuration is automatically set in `terragrunt.hcl` based on `var.env`.

## Troubleshooting

### GitHub Actions Failures

1. Check workflow logs in Actions tab
2. Verify GitHub Secrets are configured
3. Ensure environment variables in `.env` files are correct
4. Check AWS IAM role permissions
5. Verify self-hosted runner is available

### Terragrunt Issues

```bash
# Clear Terragrunt cache
rm -rf .terragrunt-cache/

# Re-initialize
terragrunt init

# Check for errors
terragrunt validate
```

### Script Deployment Issues

1. **Glue scripts not found**: Check S3 bucket for uploaded scripts
   ```bash
   aws s3 ls s3://code-bucket/glue/scripts/
   ```

2. **Lambda import errors**: Verify shared libraries are in package
   ```bash
   unzip -l module/aws/rules-engine/lambda_packages/rule_executor.zip | grep -E "(connectors|rules|metadata|utils)"
   ```

3. **Missing dependencies**: Ensure all imports use relative paths from shared directory

## Making Changes to Scripts

### Updating Glue Scripts

1. Edit script in `module/aws/rules-engine/modules/glue/scripts/`
2. Commit and push
3. Deploy via GitHub Actions or `terragrunt apply`
4. Terraform will detect changes and re-upload to S3

### Updating Lambda Functions

1. Edit code in `module/aws/rules-engine/modules/lambda/scripts/{lambda_name}/`
2. Commit and push
3. Deploy via GitHub Actions or `terragrunt apply`
4. Terraform will detect changes and re-package Lambda

### Updating Shared Libraries

1. Edit code in `module/aws/rules-engine/shared/`
2. Commit and push
3. Deploy via GitHub Actions or `terragrunt apply`
4. Terraform will detect changes and update both Lambda and Glue

## Best Practices

1. **Always review Terragrunt plan** before applying
2. **Use separate workspaces** for dev/test/prod
3. **Tag all resources** for cost tracking
4. **Use secrets management** (Secrets Manager) for sensitive data
5. **Enable versioning** on S3 buckets
6. **Set up CloudWatch alarms** for monitoring
7. **Regular backups** of Terragrunt state
8. **Protect production environment** with approval requirements
9. **Test script changes** in dev before deploying to prod

## Security Considerations

- Never commit `.env` files with secrets
- Use AWS Secrets Manager for passwords
- Enable encryption at rest for RDS and S3
- Use VPC endpoints for AWS service access
- Restrict IAM permissions to minimum required
- Enable CloudTrail for audit logging
- Use OIDC for AWS authentication (no long-lived credentials)

## Workflow Details

The reusable workflow (`.github/workflows/deploy.yml`) is called by the main workflow (`.github/workflows/workflow.yml`) with:

- `environment`: Target environment (dev/test/prod)
- `action`: Terraform action (plan/apply/destroy)
- `module`: Module name (`rules-engine`)

The workflow uses the shared action `zilvertonz/shared-github-actions/deploy/terragrunt@v0` which handles:
- Terragrunt initialization
- Terraform workspace management
- State locking
- Plan/apply/destroy operations
- Automatic script packaging and deployment
