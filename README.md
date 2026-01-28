# Data Rules Engine Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Terraform](https://img.shields.io/badge/terraform-1.5%2B-purple)](https://www.terraform.io/)

A production-grade, metadata-driven data validation and rules engine framework for AWS, supporting multiple data sources with comprehensive logging, monitoring, and a web-based management interface.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Deployment](#detailed-deployment)
- [Project Structure](#project-structure)
- [Component Overview](#component-overview)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Monitoring & Operations](#monitoring--operations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Data Rules Engine Framework is an enterprise-ready solution for data quality validation across heterogeneous data sources. It enables organizations to:

- Define validation rules once and reuse them across multiple tables and columns
- Connect to various data sources (Databricks, SQL Server, Teradata, S3, Redshift, Aurora)
- Execute validations at scale using AWS serverless services
- Track validation results over time with comprehensive audit trails
- Manage rules through an intuitive web interface or batch imports

### What Problems Does It Solve?

1. **Data Quality at Scale**: Validate millions of records across multiple data sources
2. **Rule Reusability**: Define rules once, apply everywhere
3. **Centralized Governance**: Single source of truth for validation logic
4. **Observability**: Track data quality trends over time
5. **Automation**: Schedule validations and receive alerts automatically

## Key Features

### Core Capabilities

- ✅ **Multi-Source Support**: Connect to 10+ data source types
- ✅ **Flexible Rule Types**: Single-field, multi-field, and cross-table validations
- ✅ **Metadata-Driven**: All rules stored in centralized metadata repository
- ✅ **Serverless Architecture**: Scales automatically using AWS Lambda and Glue
- ✅ **Web UI**: Intuitive interface for rule management
- ✅ **Batch Import**: Upload rules via CSV/Excel
- ✅ **Comprehensive Logging**: Track every validation execution
- ✅ **Real-time Alerts**: Get notified of critical failures
- ✅ **API Access**: RESTful API for programmatic integration

### Technical Features

- 🔧 **Infrastructure as Code**: Complete Terraform/Terragrunt deployment
- 🔧 **High Availability**: Multi-AZ deployment with automatic failover
- 🔧 **Security**: Encryption at rest and in transit, IAM-based access control
- 🔧 **Performance**: Parallel execution, partition pruning, caching
- 🔧 **Extensibility**: Plugin architecture for custom connectors and rules

## Architecture

### High-Level Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Web UI     │─────▶│ API Gateway  │─────▶│   Lambda    │
│ (CloudFront)│      │  (REST API)  │      │  Functions  │
└─────────────┘      └──────────────┘      └──────┬──────┘
                                                   │
                     ┌─────────────────────────────┼─────────────┐
                     │                             │             │
              ┌──────▼──────┐            ┌────────▼────────┐   ┌▼─────────┐
              │   Glue Jobs │            │ Step Functions  │   │   SNS    │
              │(PySpark ETL)│            │  (Orchestration)│   │(Alerts)  │
              └──────┬──────┘            └────────┬────────┘   └──────────┘
                     │                             │
              ┌──────▼──────────────────────────────▼──────┐
              │          Metadata Repository              │
              │        (Aurora PostgreSQL)                │
              └───────────────────────────────────────────┘
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       │                          │                          │
┌──────▼──────┐          ┌───────▼────────┐         ┌──────▼──────┐
│ Databricks  │          │   SQL Server   │         │  Redshift   │
│             │          │                │         │             │
└─────────────┘          └────────────────┘         └─────────────┘
```

### Component Interaction Flow

1. **User Interaction**: User creates/manages rules via Web UI
2. **API Layer**: Requests routed through API Gateway to Lambda
3. **Orchestration**: EventBridge triggers scheduled validations
4. **Execution**: Lambda spawns Glue jobs for data processing
5. **Data Access**: Glue jobs connect to data sources via connectors
6. **Validation**: Rules executed against datasets using PySpark
7. **Storage**: Results stored in metadata DB and S3
8. **Notification**: Critical failures trigger SNS alerts

For detailed architecture diagrams, see [ARCHITECTURE.md](ARCHITECTURE.md)

## Prerequisites

### Required Tools

- **AWS Account** with appropriate permissions
- **Terraform** >= 1.5.0 ([Install Guide](https://www.terraform.io/downloads))
- **Terragrunt** >= 0.48.0 ([Install Guide](https://terragrunt.gruntwork.io/docs/getting-started/install/))
- **Python** >= 3.9 ([Download](https://www.python.org/downloads/))
- **Node.js** >= 16.x (for UI) ([Download](https://nodejs.org/))
- **AWS CLI** >= 2.x ([Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html))
- **Docker** (for local development) ([Install Guide](https://docs.docker.com/get-docker/))

### AWS Permissions

Your AWS user/role needs permissions for:
- VPC, Subnets, Security Groups
- RDS (Aurora PostgreSQL)
- Lambda, Glue, Step Functions
- S3, Secrets Manager
- API Gateway, CloudFront
- IAM (role/policy creation)
- CloudWatch Logs and Metrics
- SNS, EventBridge

### AWS Service Quotas

Ensure you have sufficient quotas for:
- Lambda concurrent executions: 100+
- Glue DPU: 50+
- RDS database instances: 5+

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/data-rules-engine.git
cd data-rules-engine
```

### 2. Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and Region
```

### 3. Initialize Terraform Backend

```bash
cd terraform
terraform init
```

### 4. Configure Environment Variables

```bash
# Copy example configuration
cp config/dev.yaml.example config/dev.yaml

# Edit configuration with your values
vim config/dev.yaml
```

Required configurations:
- AWS region
- VPC CIDR (if creating new VPC)
- Database credentials
- Notification email addresses

### 5. Deploy Infrastructure

```bash
# Bootstrap (creates S3 backend and DynamoDB for state locking)
./scripts/bootstrap.sh

# Deploy to dev environment
cd terragrunt/envs/dev
terragrunt apply
```

Deployment takes approximately 15-20 minutes.

### 6. Initialize Database

```bash
# Run database migrations
./scripts/run_migrations.sh dev

# Seed with sample data (optional)
python scripts/seed_metadata.py --env dev
```

### 7. Access the Web UI

After deployment, Terragrunt outputs the CloudFront URL:

```bash
# Get the UI URL
cd terragrunt/envs/dev
terragrunt output ui_url

# Example output: https://d1234567890.cloudfront.net
```

Navigate to this URL in your browser. Default credentials are output separately.

### 8. Create Your First Rule

See [User Guide - Creating Rules](docs/user_guide.md#creating-rules)

## Detailed Deployment

### Environment Setup

The framework supports multiple environments (dev, test, prod) using Terragrunt.

#### 1. Configure Backend

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

#### 2. Environment-Specific Configuration

Edit `terragrunt/envs/dev/terragrunt.hcl`:

```hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../terraform"
}

inputs = {
  environment              = "dev"
  aws_region              = "us-east-1"
  
  # VPC Configuration
  create_vpc              = true
  vpc_cidr                = "10.0.0.0/16"
  
  # RDS Configuration
  database_instance_class = "db.t3.medium"
  database_allocated_storage = 20
  database_name           = "rules_engine_dev"
  
  # Lambda Configuration
  lambda_memory_size      = 512
  lambda_timeout          = 300
  
  # Glue Configuration
  glue_max_capacity       = 10
  glue_worker_type         = "G.1X"
  
  # Tags
  tags = {
    Environment = "dev"
    Project     = "DataRulesEngine"
    ManagedBy   = "Terraform"
  }
}
```

#### 3. Deploy Step-by-Step

```bash
# Navigate to environment
cd terragrunt/envs/dev

# Review plan
terragrunt plan

# Apply infrastructure
terragrunt apply

# Confirm with 'yes'
```

#### 4. Post-Deployment Steps

```bash
# 1. Run database migrations
./scripts/run_migrations.sh dev

# 2. Package and deploy Lambda functions
./scripts/build_lambdas.sh

# 3. Build and deploy UI
cd src/ui/frontend
npm install
npm run build
aws s3 sync build/ s3://$(cd ../../../terragrunt/envs/dev && terragrunt output -raw ui_bucket_name)

# 4. Create CloudFront invalidation
aws cloudfront create-invalidation \
  --distribution-id $(cd terragrunt/envs/dev && terragrunt output -raw cloudfront_distribution_id) \
  --paths "/*"
```

### Updating Infrastructure

```bash
# Make changes to terraform files or variables
vim terragrunt/envs/dev/terragrunt.hcl

# Review changes
terragrunt plan

# Apply updates
terragrunt apply
```

### Destroying Infrastructure

```bash
# Destroy specific environment
cd terragrunt/envs/dev
terragrunt destroy

# Or use the script
./scripts/destroy.sh dev
```

## Project Structure

### How Files Are Organized and Linked

#### 1. Infrastructure Layer (`terraform/`)

**Purpose**: Defines all AWS infrastructure as code

**Key Files**:
- `main.tf`: Main orchestrator, includes all resource modules
- `variables.tf`: Input parameters (VPC CIDR, instance sizes, etc.)
- `outputs.tf`: Exported values (URLs, ARNs, connection strings)
- `modules/database/main.tf`: Aurora PostgreSQL cluster definition
- `modules/lambda/main.tf`: Lambda function resources
- `modules/glue/main.tf`: Glue job definitions

**How They Link**:
```
main.tf
  ├─▶ modules/database (creates database)
  │     └─▶ outputs DB endpoint to outputs.tf
  ├─▶ modules/lambda (creates functions)
  │     └─▶ references DB endpoint from database module
  ├─▶ modules/glue (creates jobs)
  │     └─▶ references S3 buckets from s3 module
  └─▶ modules/iam (creates roles)
        └─▶ referenced by lambda and glue modules
```

#### 2. Application Layer (`src/`)

**Purpose**: Business logic and application code

**Key Components**:

**Connectors** (`src/connectors/`):
- `base.py`: Abstract interface all connectors implement
- `factory.py`: Creates appropriate connector based on source type
- `databricks.py`, `sqlserver.py`, etc.: Concrete implementations

**Rules Engine** (`src/rules/`):
- `executor.py`: Orchestrates rule execution
- `parser.py`: Parses rule expressions
- `single_field.py`, `multi_field.py`: Execution strategies

**Metadata** (`src/metadata/`):
- `models.py`: SQLAlchemy ORM models (database schema)
- `repository.py`: Data access layer

#### 3. Lambda Functions (`src/lambda/`)

**Purpose**: Serverless handlers for different tasks

**How They Link**:
```
rule_executor/handler.py
  ├─▶ uses metadata.repository to fetch rules
  ├─▶ uses connectors.factory to create connectors
  └─▶ triggers glue jobs via boto3

api_gateway/app.py
  ├─▶ uses metadata.repository for CRUD
  └─▶ returns JSON to API Gateway
```

#### 4. Glue Jobs (`src/glue/`)

**Purpose**: Heavy data processing tasks

**How They Execute**:
```
EventBridge triggers Lambda (rule_executor)
  ↓
Lambda starts Glue Job via boto3
  ↓
Glue Job (bulk_validator.py) runs:
  ├─▶ imports from src/connectors
  ├─▶ imports from src/rules
  ├─▶ reads from metadata DB
  ├─▶ processes data with PySpark
  └─▶ writes results to S3 and metadata DB
```

#### 5. Database Schema (`sql/`)

**Purpose**: Defines metadata repository structure

**Execution Order**:
```
scripts/run_migrations.sh
  ├─▶ connects to Aurora (endpoint from terraform output)
  ├─▶ runs sql/metadata_schema.sql
  └─▶ optionally runs seed data
```

## Component Overview

### AWS Lambda Functions

#### 1. Rule Executor (`src/lambda/rule_executor/`)

**Purpose**: Orchestrates validation execution
**Triggered by**: EventBridge schedule, API Gateway
**Does**:
- Fetches active rule assignments from metadata DB
- Determines execution strategy (Lambda vs Glue)
- Spawns Glue jobs for large datasets
- Handles small validations directly

#### 2. API Backend (`src/lambda/api_gateway/`)

**Purpose**: Provides REST API for UI
**Routes**:
```
GET    /api/rules              # List rules
POST   /api/rules              # Create rule
PUT    /api/rules/{id}         # Update rule
DELETE /api/rules/{id}         # Delete rule
GET    /api/results            # Query validation results
POST   /api/execute            # Trigger ad-hoc validation
GET    /api/sources            # List data sources
POST   /api/batch-import       # Upload CSV of rules
```

### AWS Glue Jobs

#### 1. Bulk Validator (`src/glue/bulk_validator.py`)

**Purpose**: Execute validations on large datasets
**Input**: Rule assignment IDs (passed as job parameters)
**Process**:
```python
1. Read rule assignments from metadata DB
2. For each assignment:
   - Create appropriate connector
   - Read source data into Spark DataFrame
   - Apply validation rules using PySpark
   - Identify failed records
   - Write results to S3 (partitioned by date)
   - Update metadata DB with summary stats
3. Generate execution summary
```

**Output**:
- Detailed results in S3: `s3://results-bucket/validations/date=YYYY-MM-DD/rule_id=123/`
- Summary in metadata DB: `validation_results` table

### Metadata Database Schema

#### Core Tables:

**data_sources**: Connection configurations for data sources
**validation_rules**: Rule definitions (reusable)
**rule_assignments**: Assignment of rules to specific tables/columns
**validation_results**: Results of validation executions

See `sql/metadata_schema.sql` for complete schema definition.

## Configuration

### Environment Variables

**Lambda Functions**:
```bash
METADATA_DB_SECRET_ARN        # Aurora connection details
AWS_REGION                    # Deployment region
S3_CODE_BUCKET               # Lambda code location
S3_RESULTS_BUCKET            # Validation results storage
GLUE_JOB_NAME                # Glue job to trigger
LOG_LEVEL                    # DEBUG, INFO, WARN, ERROR
```

**Glue Jobs**:
```bash
--metadata-db-secret-arn     # Database connection
--s3-results-bucket          # Where to write results
--rule-assignment-ids        # Which rules to execute (runtime param)
```

### Configuration Files

**config/dev.yaml**:
```yaml
environment: dev
aws_region: us-east-1

database:
  instance_class: db.t3.medium
  allocated_storage: 20
  backup_retention_days: 7
  
lambda:
  memory_size: 512
  timeout: 300
  reserved_concurrency: 50

glue:
  worker_type: G.1X
  number_of_workers: 10
  timeout: 2880  # 48 hours

notifications:
  email_recipients:
    - data-team@company.com
  sns_topic_name: rules-engine-alerts

tags:
  Project: DataRulesEngine
  Environment: dev
  CostCenter: Engineering
```

## Usage

### Creating Rules via UI

1. **Navigate to Rule Library**: Click "Rules" in sidebar
2. **Click "Create New Rule"**
3. **Fill in details**:
   - Name: "Email Format Validation"
   - Type: "Single Field"
   - Category: "Accuracy"
   - Severity: "High"
4. **Define logic**:
   ```sql
   column RLIKE '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
   ```
5. **Save Rule**

### Assigning Rules to Tables

1. **Click "Assignments"** in sidebar
2. **Click "New Assignment"**
3. **Select**:
   - Data Source: "Production Database"
   - Schema: "customer_data"
   - Table: "users"
   - Columns: ["email"]
   - Rule: "Email Format Validation"
   - Frequency: "Daily at 2 AM"
4. **Save Assignment**

### Creating Rules via API

```bash
curl -X POST https://api.rules-engine.com/api/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_name": "Age Range Check",
    "rule_type": "single_field",
    "rule_logic": "column BETWEEN 0 AND 120",
    "severity_level": "high",
    "is_reusable": true
  }'
```

### Batch Import Rules

1. **Prepare CSV**:
```csv
rule_name,rule_type,rule_logic,severity,target_table,target_columns
"Not Null Check",single_field,"column IS NOT NULL",critical,users,"email,username"
"Phone Format",single_field,"column RLIKE '^\\d{10}$'",high,users,phone_number
```

2. **Upload via UI**: Click "Batch Import" → Select file → Submit

3. **Or via API**:
```bash
curl -X POST https://api.rules-engine.com/api/batch-import \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@rules.csv"
```

### Viewing Validation Results

**Via UI**:
1. Click "Results" in sidebar
2. Filter by date range, rule name, table name, status
3. Click row to see details

**Via API**:
```bash
curl -X GET "https://api.rules-engine.com/api/results?start_date=2024-01-01&status=fail" \
  -H "Authorization: Bearer $TOKEN"
```

## Development

### Local Setup

```bash
# Clone repository
git clone https://github.com/your-org/data-rules-engine.git
cd data-rules-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Set up local database (Docker)
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Seed test data
python scripts/seed_metadata.py --env local
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_connectors.py

# Run integration tests (requires AWS credentials)
pytest tests/integration/ --aws-profile=dev
```

### Code Style

```bash
# Format code
black src/ tests/

# Lint
pylint src/
flake8 src/

# Type checking
mypy src/
```

## Monitoring & Operations

### CloudWatch Dashboards

The deployment creates dashboards for monitoring:

**Metrics**:
- Lambda invocations and errors
- Glue job runs and failures
- API Gateway requests and latency
- RDS CPU and connections
- Validation pass/fail rates

### CloudWatch Logs

**Log Groups**:
```
/aws/lambda/rules-executor
/aws/lambda/api-backend
/aws-glue/jobs/bulk-validator
```

**Querying Logs**:
```bash
# View recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/rules-executor \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### Alarms

**Critical Alarms**:
- Lambda errors > 5 in 5 minutes
- Glue job failures
- API Gateway 5xx errors > 1%
- RDS CPU > 80%
- Validation failure rate > 10%

## Troubleshooting

### Common Issues

#### 1. Lambda Timeout Errors

**Symptom**: `Task timed out after 300.00 seconds`

**Solution**:
- For large validations, increase Lambda timeout in `config/*.yaml`
- Or delegate to Glue job instead

#### 2. Glue Job OOM Errors

**Symptom**: `Container killed on request. Exit code is 137`

**Solution**: Increase Glue capacity in configuration

#### 3. Database Connection Errors

**Symptom**: `could not connect to server: Connection timed out`

**Causes**:
- Lambda not in VPC with DB access
- Security group rules blocking traffic

**Solution**: Verify security group configuration

### Debugging

**Enable Debug Logging**:
```bash
aws lambda update-function-configuration \
  --function-name rules-executor \
  --environment "Variables={LOG_LEVEL=DEBUG}"
```

**Tail Logs in Real-Time**:
```bash
aws logs tail /aws/lambda/rules-executor --follow
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/development/contributing.md)

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run tests: `pytest`
5. Commit: `git commit -am 'Add new feature'`
6. Push: `git push origin feature/my-feature`
7. Create Pull Request

## License

MIT License - see [LICENSE](LICENSE) file

---

## Quick Reference

### Important URLs (After Deployment)

```bash
# Get all outputs
cd terragrunt/envs/dev
terragrunt output

# Specific outputs
UI URL:              $(terragrunt output -raw ui_url)
API Endpoint:        $(terragrunt output -raw api_endpoint)
Database Endpoint:   $(terragrunt output -raw db_endpoint)
```

### Common Commands

```bash
# Deploy
./scripts/deploy.sh dev

# Update Lambda
./scripts/build_lambdas.sh && terragrunt apply

# Run migrations
./scripts/run_migrations.sh dev

# Tail logs
aws logs tail /aws/lambda/rules-executor --follow
```

### Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/data-rules-engine/issues)
- **Email**: data-platform-team@company.com
