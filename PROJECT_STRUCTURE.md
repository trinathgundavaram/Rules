# Project Structure

## Restructured for Terragrunt + Co-located Scripts

This document describes the project structure after restructuring for Terragrunt deployment with scripts co-located with their infrastructure components.

## Directory Structure

```
Rules/
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI workflow (linting, testing)
│       ├── deploy.yml          # Reusable deployment workflow (workflow_call)
│       └── workflow.yml        # Main workflow that calls deploy.yml
│
├── module/                     # Infrastructure modules
│   └── aws/
│       └── rules-engine/       # Terragrunt module
│           ├── main.tf         # Main infrastructure
│           ├── variables.tf    # Input variables
│           ├── outputs.tf      # Output values
│           ├── versions.tf     # Provider versions
│           ├── terragrunt.hcl  # Terragrunt configuration
│           ├── lambda_packages/ # Lambda ZIP files (gitignored)
│           │
│           ├── shared/         # Shared Python libraries
│           │   ├── connectors/ # Data source connectors
│           │   ├── rules/      # Rules engine core
│           │   ├── metadata/   # Database models & repository
│           │   └── utils/      # Utilities
│           │
│           └── modules/        # Reusable Terraform modules
│               ├── glue/
│               │   ├── main.tf
│               │   ├── variables.tf
│               │   ├── outputs.tf
│               │   └── scripts/  # Glue job scripts
│               │       ├── __init__.py
│               │       └── bulk_validator.py
│               │
│               ├── lambda/
│               │   ├── main.tf
│               │   ├── variables.tf
│               │   ├── outputs.tf
│               │   └── scripts/  # Lambda function code
│               │       ├── rule_executor/
│               │       │   ├── __init__.py
│               │       │   └── handler.py
│               │       └── api_gateway/
│               │           ├── __init__.py
│               │           └── app.py
│               │
│               ├── s3/
│               ├── database/
│               ├── api_gateway/
│               ├── iam/
│               ├── secrets/
│               ├── eventbridge/
│               └── monitoring/
│
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test fixtures
│
├── sql/                        # Database schema
│   └── metadata_schema.sql     # Initial database schema
│
├── config/                     # Application configuration
│   ├── dev.yaml
│   └── prod.yaml
│
├── examples/                   # Example usage
│   └── basic_usage.py
│
├── docs/                       # Documentation
│   ├── architecture.md
│   └── user_guide.md
│
├── .env.common                 # Common environment variables
├── .env.dev                    # Dev environment variables
├── .env.test                   # Test environment variables
├── .env.prod                   # Prod environment variables
│
├── .gitignore                  # Git ignore rules
├── README.md                   # Main documentation
├── DEPLOYMENT.md               # Deployment guide
├── PROJECT_STRUCTURE.md        # This file
├── requirements.txt            # Python dependencies
├── setup.py                    # Python package setup
├── pytest.ini                  # Pytest configuration
└── run_tests.sh                # Test runner script
```

## Files Removed

The following files/directories were removed during restructuring:

- ❌ `src/` directory - Moved to `module/aws/rules-engine/shared/` and module-specific folders
- ❌ `scripts/` directory - Removed packaging script (Terraform handles it now)
- ❌ `terraform/` directory - Moved to `module/aws/rules-engine/`
- ❌ `terraform/deploy.sh` - Not needed with GitHub Actions
- ❌ `terraform/terraform.tfvars.*` - Using Terragrunt inputs instead

## Files Added/Updated

- ✅ `module/aws/rules-engine/` - Complete Terraform module structure
- ✅ `module/aws/rules-engine/shared/` - Shared Python libraries
- ✅ `module/aws/rules-engine/modules/glue/scripts/` - Glue job scripts
- ✅ `module/aws/rules-engine/modules/lambda/scripts/` - Lambda function code
- ✅ `module/aws/rules-engine/terragrunt.hcl` - Terragrunt configuration
- ✅ `.github/workflows/deploy.yml` - Reusable workflow (workflow_call)
- ✅ `.github/workflows/workflow.yml` - Main workflow that calls deploy.yml
- ✅ `.env.*` files - Environment variable files (gitignored)
- ✅ Updated `README.md` - Focused on new structure
- ✅ Updated `DEPLOYMENT.md` - Comprehensive deployment guide
- ✅ Updated `.gitignore` - Added Terragrunt and package-specific ignores

## Key Features

### Script Co-location

**Glue Scripts**:
- Located in `module/aws/rules-engine/modules/glue/scripts/`
- Automatically uploaded to S3 by Terraform
- Shared libraries uploaded separately and referenced via `--extra-py-files`

**Lambda Functions**:
- Located in `module/aws/rules-engine/modules/lambda/scripts/`
- Automatically packaged with shared libraries by Terraform
- ZIP files created in `lambda_packages/` directory

**Shared Libraries**:
- Located in `module/aws/rules-engine/shared/`
- Automatically included in both Lambda and Glue deployments
- No manual copying or packaging needed

### Reusable GitHub Actions Workflow

The `.github/workflows/deploy.yml` workflow is a **reusable workflow** (workflow_call) that:
- Accepts inputs: `environment`, `action`, `module`
- Runs on self-hosted runner: `MA-Analytics-Runner`
- Uses OIDC for AWS authentication
- Loads environment variables from `.env` files
- Executes Terragrunt actions (Terraform handles script packaging)

### Main Workflow

The `.github/workflows/workflow.yml` workflow:
- Triggers on push/PR to main/develop
- Runs CI checks (linting, testing)
- Calls the reusable deploy workflow
- Supports manual workflow dispatch

### Terragrunt Module

The module at `module/aws/rules-engine/`:
- Contains all Terraform code
- Contains all application scripts
- Uses Terragrunt for configuration management
- Maps GitHub Actions variables to Terraform variables
- Generates provider configuration dynamically
- Sets environment-specific defaults

## Deployment Flow

```
Developer Push/PR
    ↓
GitHub Actions (workflow.yml)
    ↓
[CI Checks] → [Lint] → [Test] → [Validate]
    ↓
Manual Trigger or Auto (if main/develop)
    ↓
Call Reusable Workflow (deploy.yml)
    ↓
[Load Env Vars] → [OIDC Auth] → [Terragrunt Plan/Apply]
    ↓
Terraform Operations:
  ├─▶ Package Lambda functions (with shared libs)
  ├─▶ Upload Glue scripts to S3
  ├─▶ Upload shared libraries to S3
  └─▶ Deploy infrastructure
    ↓
Infrastructure Deployed
    ↓
[Initialize DB] → [Verify] → [Output Results]
```

## Script Deployment Details

### Glue Scripts

1. **Source**: `module/aws/rules-engine/modules/glue/scripts/*.py`
2. **Terraform Action**: Uploads to `s3://code-bucket/glue/scripts/`
3. **Shared Libs**: Uploads to `s3://code-bucket/glue/shared/`
4. **Glue Job Config**: References S3 script path, includes shared libs via `--extra-py-files`

### Lambda Functions

1. **Source**: `module/aws/rules-engine/modules/lambda/scripts/{lambda_name}/`
2. **Terraform Action**:
   - Copies Lambda code to temp directory
   - Copies shared libraries to temp directory
   - Creates ZIP archive
   - Deploys to Lambda
3. **Package Location**: `module/aws/rules-engine/lambda_packages/{lambda_name}.zip`

## Environment Variables

### Required in `.env.*` files:

- `REGION`: AWS region
- `ACCOUNT_NUMBER`: AWS account number
- `TF_VERSION`: Terraform version
- `TG_VERSION`: Terragrunt version
- `VPC_ID`: VPC ID (optional, can be in Terragrunt)
- `DATABASE_SUBNET_IDS`: Comma-separated subnet IDs
- `LAMBDA_SUBNET_IDS`: Comma-separated subnet IDs

### GitHub Secrets:

- `ORG_REPO_READ_ACCESS`: Token for private repos
- `TF_VAR_TDV_PASSWORD_DEV`: Dev database password
- `TF_VAR_TDV_PASSWORD_TEST`: Test database password
- `TF_VAR_TDV_PASSWORD_PROD`: Prod database password
- `ETL_OSS_TDV_PROD`: Production ETL token

## Module Configuration

The Terragrunt configuration (`module/aws/rules-engine/terragrunt.hcl`) automatically:
- Maps `TF_VAR_env` → `var.env` → `local.env`
- Maps `TF_VAR_region` → `var.region`
- Sets environment-specific defaults:
  - Dev: Smaller instances, fewer workers
  - Prod: Larger instances, more workers
- Configures resource tags with repo/branch info

## Next Steps

1. **Create `.env` files**: Add environment variables
2. **Configure GitHub Secrets**: Add required secrets
3. **Set up GitHub Environments**: Configure dev/test/prod
4. **Deploy**: Use GitHub Actions workflow or Terragrunt locally
5. **Initialize Database**: Run `sql/metadata_schema.sql`

## Maintenance

- **Update Scripts**: Edit in `module/aws/rules-engine/modules/{glue|lambda}/scripts/`
- **Update Shared Libraries**: Edit in `module/aws/rules-engine/shared/`
- **Update Dependencies**: Update `requirements.txt` and run tests
- **Terraform Updates**: Modify modules in `module/aws/rules-engine/modules/`
- **Add Tests**: Add to `tests/unit/` or `tests/integration/`
- **Documentation**: Update `README.md` and `DEPLOYMENT.md`
- **Environment Variables**: Update `.env.*` files as needed

## Benefits of This Structure

1. **Co-location**: Scripts are with their infrastructure, easier to find and maintain
2. **Automatic Deployment**: Terraform handles all packaging and deployment
3. **No Manual Steps**: No separate packaging scripts needed
4. **Version Control**: All code in one place, easier to track changes
5. **Consistency**: Same deployment process for all components
6. **Shared Libraries**: Automatically included, no manual copying
