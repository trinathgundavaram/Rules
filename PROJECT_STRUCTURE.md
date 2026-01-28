# Project Structure

## Restructured for Terragrunt + Reusable GitHub Actions Workflow

This document describes the project structure after restructuring for Terragrunt deployment with reusable GitHub Actions workflows.

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
│           ├── outputs.tf     # Output values
│           ├── versions.tf    # Provider versions
│           ├── terragrunt.hcl # Terragrunt configuration
│           ├── lambda_packages/ # Lambda ZIP files (gitignored)
│           └── modules/       # Reusable Terraform modules
│               ├── s3/
│               ├── database/
│               ├── lambda/
│               ├── glue/
│               ├── api_gateway/
│               ├── iam/
│               ├── secrets/
│               ├── eventbridge/
│               └── monitoring/
│
├── src/                        # Application source code
│   ├── connectors/             # Data source connectors
│   │   ├── base.py
│   │   ├── databricks.py
│   │   ├── sqlserver.py
│   │   ├── teradata.py
│   │   ├── s3.py
│   │   ├── redshift.py
│   │   ├── aurora_postgresql.py
│   │   └── factory.py
│   │
│   ├── rules/                  # Rules engine core
│   │   ├── executor.py
│   │   ├── parser.py
│   │   ├── single_field.py
│   │   ├── multi_field.py
│   │   └── functions.py
│   │
│   ├── metadata/               # Database models & repository
│   │   ├── models.py
│   │   └── repository.py
│   │
│   ├── lambda/                 # Lambda functions
│   │   ├── rule_executor/
│   │   │   └── handler.py
│   │   └── api_gateway/
│   │       └── app.py
│   │
│   ├── glue/                   # Glue jobs
│   │   └── bulk_validator.py
│   │
│   └── utils/                  # Utilities
│       ├── logger.py
│       ├── metrics.py
│       ├── exceptions.py
│       └── batch_import.py
│
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test fixtures
│
├── scripts/                    # Utility scripts
│   └── package_lambdas.sh     # Lambda packaging script
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

- ❌ `terraform/` directory - Moved to `module/aws/rules-engine/`
- ❌ `terraform/deploy.sh` - Not needed with GitHub Actions
- ❌ `terraform/README.md` - Merged into main README
- ❌ `terraform/terraform.tfvars.*` - Using Terragrunt inputs instead
- ❌ Old `deploy.yml` - Replaced with reusable workflow_call pattern

## Files Added/Updated

- ✅ `module/aws/rules-engine/` - Complete Terraform module structure
- ✅ `module/aws/rules-engine/terragrunt.hcl` - Terragrunt configuration
- ✅ `.github/workflows/deploy.yml` - Reusable workflow (workflow_call)
- ✅ `.github/workflows/workflow.yml` - Main workflow that calls deploy.yml
- ✅ `.env.*` files - Environment variable files (gitignored)
- ✅ Updated `README.md` - Focused on Terragrunt + GitHub Actions
- ✅ Updated `DEPLOYMENT.md` - Comprehensive deployment guide
- ✅ Updated `.gitignore` - Added Terragrunt-specific ignores
- ✅ Updated `scripts/package_lambdas.sh` - Updated paths for module structure

## Key Features

### Reusable GitHub Actions Workflow

The `.github/workflows/deploy.yml` workflow is a **reusable workflow** (workflow_call) that:
- Accepts inputs: `environment`, `action`, `module`
- Runs on self-hosted runner: `MA-Analytics-Runner`
- Uses OIDC for AWS authentication
- Loads environment variables from `.env` files
- Packages Lambda functions
- Executes Terragrunt actions

### Main Workflow

The `.github/workflows/workflow.yml` workflow:
- Triggers on push/PR to main/develop
- Runs CI checks (linting, testing)
- Calls the reusable deploy workflow
- Supports manual workflow dispatch

### Terragrunt Module

The module at `module/aws/rules-engine/`:
- Contains all Terraform code
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
[Load Env Vars] → [OIDC Auth] → [Package Lambdas] → [Terragrunt Plan/Apply]
    ↓
Infrastructure Deployed
    ↓
[Initialize DB] → [Verify] → [Output Results]
```

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
6. **Package Lambdas**: Run `./scripts/package_lambdas.sh` (or let GitHub Actions do it)

## Maintenance

- **Update Dependencies**: Update `requirements.txt` and run tests
- **Terraform Updates**: Modify modules in `module/aws/rules-engine/modules/`
- **Add Tests**: Add to `tests/unit/` or `tests/integration/`
- **Documentation**: Update `README.md` and `DEPLOYMENT.md`
- **Environment Variables**: Update `.env.*` files as needed
