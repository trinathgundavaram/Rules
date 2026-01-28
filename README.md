# Production-Grade Metadata-Driven Rules Engine Framework

A comprehensive, enterprise-ready data validation and rules engine framework for multi-source data quality management.

## Features

- **Metadata-Driven**: Centralized rule configuration stored in Aurora PostgreSQL
- **Multi-Source Support**: Databricks, SQL Server, Teradata, S3, Aurora PostgreSQL, Redshift
- **AWS-Native**: Built on Lambda, Glue, S3, RDS, and other AWS services
- **Web UI**: React-based interface for rule management and visualization
- **Flexible Rules**: Single-field, multi-field, and cross-table validation rules
- **Comprehensive Logging**: Detailed audit trails and CloudWatch integration
- **Scalable**: Designed to handle 100+ concurrent validations and datasets up to 1TB

## Architecture

```
┌─────────────────┐
│   Web UI (React)│
└────────┬────────┘
         │
┌────────▼────────┐
│  API Gateway    │
│  (Lambda)       │
└────────┬────────┘
         │
┌────────▼──────────────────────────────────┐
│         Rules Engine Core                  │
│  ┌────────────┐  ┌──────────────────┐    │
│  │ Executor   │  │ Rule Parser      │    │
│  └────────────┘  └──────────────────┘    │
└────────┬──────────────────────────────────┘
         │
┌────────▼──────────────────────────────────┐
│      Data Connector Framework             │
│  Databricks │ SQL Server │ Teradata │ S3 │
└────────┬──────────────────────────────────┘
         │
┌────────▼────────┐  ┌──────────────────┐
│  Metadata DB    │  │  AWS Glue Jobs   │
│  (Aurora PG)    │  │  (Bulk Processing)│
└─────────────────┘  └──────────────────┘
```

## Project Structure

```
rules-engine-framework/
├── src/
│   ├── connectors/      # Data source connectors
│   ├── rules/           # Rules engine core
│   ├── metadata/        # Metadata repository layer
│   ├── lambda/          # AWS Lambda functions
│   ├── glue/            # AWS Glue jobs
│   ├── utils/           # Utilities (logging, metrics, exceptions)
│   └── ui/              # Web UI (React frontend + API backend)
├── tests/               # Test suite
├── infrastructure/      # IaC (CDK/Terraform)
├── config/              # Environment configurations
├── sql/                 # Database schema
└── docs/                # Documentation
```

## Quick Start

### Prerequisites

- Python 3.9+
- AWS Account with appropriate permissions
- Aurora PostgreSQL instance
- Node.js 16+ (for UI)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd rules-engine-framework

# Install Python dependencies
pip install -r requirements.txt

# Install UI dependencies
cd src/ui/frontend
npm install

# Set up environment variables
cp config/dev.yaml.example config/dev.yaml
# Edit config/dev.yaml with your AWS credentials and DB connection
```

### Database Setup

```bash
# Connect to Aurora PostgreSQL and run schema
psql -h <aurora-endpoint> -U <username> -d <database> -f sql/metadata_schema.sql
```

### Running Locally

```bash
# Start the API server (for UI backend)
python -m src.lambda.api_gateway.app

# Start the UI (in another terminal)
cd src/ui/frontend
npm start
```

## Usage

### Creating a Rule

```python
from src.metadata.repository import MetadataRepository
from src.rules.executor import RuleExecutor

# Create a rule
repo = MetadataRepository()
rule_id = repo.create_rule(
    rule_name="Email Format Validation",
    rule_type="single_field",
    rule_category="accuracy",
    severity_level="high",
    rule_logic="regex_match(col('email'), r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$')",
    is_reusable=True
)

# Assign rule to a table
assignment_id = repo.assign_rule(
    rule_id=rule_id,
    source_id=1,
    schema_name="public",
    table_name="users",
    column_names=["email"],
    execution_frequency="batch"
)
```

### Executing Validation

```python
from src.lambda.rule_executor import handler

# Trigger validation via Lambda
event = {
    "assignment_id": assignment_id,
    "execution_type": "batch"
}
result = handler(event, {})
```

## Rule Types

### Completeness Rules
- Null checks
- Empty string validation
- Required field validation

### Accuracy Rules
- Range checks
- Regex pattern matching
- Reference data lookups

### Consistency Rules
- Cross-field validation
- Business logic rules

### Integrity Rules
- Foreign key checks
- Uniqueness constraints

### Timeliness Rules
- Data freshness checks
- SLA validation

### Custom Rules
- User-defined Python/SQL expressions

## Configuration

Configuration files are located in `config/` directory:
- `dev.yaml`: Development environment
- `test.yaml`: Test environment
- `prod.yaml`: Production environment

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src tests/
```

## Deployment

### Infrastructure Deployment

```bash
# Using AWS CDK
cd infrastructure/cdk
cdk deploy --all

# Using Terraform
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### Lambda Deployment

```bash
# Package Lambda functions
./scripts/package_lambdas.sh

# Deploy via CDK/Terraform or AWS CLI
```

## Documentation

- [Architecture Guide](docs/architecture.md)
- [User Guide](docs/user_guide.md)
- [API Reference](docs/api_reference.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Specify your license here]

## Support

For issues and questions, please open an issue in the repository.
