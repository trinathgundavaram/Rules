# Data Rules Engine Framework

[![CI](https://github.com/your-org/rules-engine/actions/workflows/workflow.yml/badge.svg)](https://github.com/your-org/rules-engine/actions/workflows/workflow.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-grade, metadata-driven data validation and rules engine framework for AWS, supporting multiple data sources with comprehensive logging, monitoring, and automated deployment via GitHub Actions with Terragrunt.

## Features

- ✅ **Metadata-Driven**: Centralized rule configuration stored in Aurora PostgreSQL
- ✅ **Multi-Source Support**: Databricks, SQL Server, Teradata, S3, Redshift, Aurora PostgreSQL
- ✅ **AWS Serverless**: Built on Lambda, Glue, S3, RDS, API Gateway
- ✅ **Infrastructure as Code**: Complete Terraform/Terragrunt deployment
- ✅ **CI/CD**: Automated deployment via GitHub Actions with reusable workflows
- ✅ **Flexible Rules**: Single-field, multi-field, and cross-table validation
- ✅ **Comprehensive Logging**: CloudWatch integration and audit trails
- ✅ **Scalable**: Handles datasets up to 1TB with parallel processing

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  API Client │─────▶│ API Gateway  │─────▶│   Lambda    │
│             │      │  (REST API)  │      │  Functions  │
└─────────────┘      └──────────────┘      └──────┬──────┘
                                                   │
                     ┌─────────────────────────────┼─────────────┐
                     │                             │             │
              ┌──────▼──────┐            ┌────────▼────────┐   ┌▼─────────┐
              │   Glue Jobs │            │  EventBridge    │   │   SNS    │
              │(PySpark ETL)│            │  (Scheduling)   │   │(Alerts)  │
              └──────┬──────┘            └─────────────────┘   └──────────┘
                     │
              ┌──────▼──────────────────────────────┐
              │          Metadata Repository         │
              │        (Aurora PostgreSQL)           │
              └─────────────────────────────────────┘
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       │                          │                          │
┌──────▼──────┐          ┌───────▼────────┐         ┌──────▼──────┐
│ Databricks  │          │   SQL Server   │         │  Redshift   │
└─────────────┘          └────────────────┘         └─────────────┘
```

## Project Structure

```
rules-engine/
├── .github/
│   └── workflows/
│       ├── ci.yml          # CI workflow (linting, testing)
│       ├── deploy.yml      # Reusable deployment workflow
│       └── workflow.yml    # Main workflow that calls deploy.yml
├── module/
│   └── aws/
│       └── rules-engine/   # Terragrunt module
│           ├── main.tf     # Main infrastructure
│           ├── variables.tf
│           ├── outputs.tf
│           ├── versions.tf
│           ├── terragrunt.hcl
│           └── modules/    # Reusable Terraform modules
├── src/                    # Application source code
│   ├── connectors/         # Data source connectors
│   ├── rules/              # Rules engine core
│   ├── metadata/           # Database models & repository
│   ├── lambda/             # Lambda functions
│   ├── glue/               # Glue jobs
│   └── utils/              # Utilities
├── tests/                  # Test suite
├── scripts/                # Utility scripts
├── sql/                    # Database schema
└── config/                 # Application configs
```

## Quick Start

### Prerequisites

- **AWS Account** with appropriate permissions
- **GitHub Repository** with Actions enabled
- **GitHub Secrets** configured (see Deployment section)
- **Python** >= 3.9 (for local development)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/rules-engine.git
   cd rules-engine
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run tests**
   ```bash
   pytest tests/unit/ -v
   ```

### Deployment via GitHub Actions

The project uses a reusable GitHub Actions workflow for deployment. The workflow is triggered automatically on push to `main` or `develop` branches, or manually via workflow dispatch.

#### Automatic Deployment

- **Push to `main` branch**: Automatically runs CI checks
- **Push to `develop` branch**: Automatically runs CI checks
- **Pull Request**: Runs CI checks only

#### Manual Deployment

1. Go to **Actions** tab in GitHub
2. Select **"Deploy Rules Engine"** workflow
3. Click **"Run workflow"**
4. Select:
   - **Environment**: `dev`, `test`, or `prod`
   - **Action**: `plan`, `apply`, or `destroy`
5. Click **"Run workflow"**

#### Required GitHub Secrets

Configure these secrets in your repository (Settings → Secrets and variables → Actions):

- `ORG_REPO_READ_ACCESS`: Token for accessing private repositories
- `TF_VAR_TDV_PASSWORD_DEV`: Database password for dev (if needed)
- `TF_VAR_TDV_PASSWORD_TEST`: Database password for test (if needed)
- `TF_VAR_TDV_PASSWORD_PROD`: Database password for prod (if needed)
- `ETL_OSS_TDV_PROD`: Production ETL OSS token (if needed)

#### Environment Variables

The workflow uses `.env` files loaded via the shared action:
- `.env.common` - Common variables
- `.env.dev` - Development environment variables
- `.env.test` - Test environment variables
- `.env.prod` - Production environment variables

Required environment variables:
- `REGION`: AWS region (e.g., `us-east-1`)
- `ACCOUNT_NUMBER`: AWS account number
- `TF_VERSION`: Terraform version (e.g., `1.5.0`)
- `TG_VERSION`: Terragrunt version (e.g., `0.48.0`)

## Usage

### Creating a Rule

```python
from src.metadata.repository import MetadataRepository

repo = MetadataRepository()
rule_id = repo.create_rule(
    rule_name="Email Format Validation",
    rule_type="single_field",
    rule_category="accuracy",
    severity_level="high",
    rule_logic="column RLIKE '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'",
    is_reusable=True
)
```

### Assigning Rules to Tables

```python
assignment_id = repo.assign_rule(
    rule_id=rule_id,
    source_id=1,
    schema_name="public",
    table_name="users",
    column_names=["email"],
    execution_frequency="daily"
)
```

### Executing Validation

Validations are automatically triggered by EventBridge schedules. You can also trigger manually via API:

```bash
curl -X POST https://api-endpoint/api/execute \
  -H "Content-Type: application/json" \
  -d '{"assignment_ids": ["assignment-123"]}'
```

## Configuration

### Terragrunt Configuration

The module configuration is in `module/aws/rules-engine/terragrunt.hcl`. It automatically:
- Maps environment variables to Terraform variables
- Configures provider settings
- Sets environment-specific defaults (instance sizes, worker counts, etc.)

### Application Configuration

Edit `config/dev.yaml` or `config/prod.yaml` for application-level settings:

```yaml
database:
  host: <from-terraform-output>
  port: 5432
  name: rules_engine_dev

aws:
  region: us-east-1
  s3:
    results_bucket: <from-terraform-output>
```

## Testing

```bash
# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html

# Run integration tests (requires AWS credentials)
pytest tests/integration/ --aws-profile=dev
```

## Monitoring

### CloudWatch Dashboards

Access CloudWatch dashboards via AWS Console:
- Lambda metrics (invocations, errors, duration)
- Glue job metrics (runs, failures, DPU hours)
- RDS metrics (CPU, connections, IOPS)
- API Gateway metrics (requests, latency, errors)

### Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/rules-executor-dev --follow

# Glue job logs
aws logs tail /aws-glue/jobs/bulk-validator-dev --follow
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black src/ tests/

# Lint
flake8 src/ tests/
```

### Making Changes

1. Create a feature branch
2. Make your changes
3. Run tests locally
4. Push to GitHub (CI will run automatically)
5. Create a pull request
6. After merge, deployment can be triggered manually

## Troubleshooting

### Deployment Fails

1. Check GitHub Actions logs
2. Verify GitHub Secrets are configured
3. Check environment variables in `.env` files
4. Verify AWS IAM role permissions

### Database Connection Issues

1. Verify security groups allow Lambda → RDS traffic
2. Check Lambda is in VPC: `aws lambda get-function-configuration`
3. Verify database endpoint from Terraform outputs

### Lambda Timeout

- Increase timeout in Terragrunt configuration
- For large datasets, ensure Glue jobs are used instead

## Documentation

- [Architecture Guide](docs/architecture.md)
- [User Guide](docs/user_guide.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Project Structure](PROJECT_STRUCTURE.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Ensure CI passes
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file

## Support

- **Documentation**: See `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/your-org/rules-engine/issues)
- **CI/CD**: Check GitHub Actions tab
