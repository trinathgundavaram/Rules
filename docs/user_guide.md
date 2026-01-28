# Rules Engine Framework - User Guide

## Getting Started

### Prerequisites

- Python 3.9+
- Aurora PostgreSQL database
- AWS Account with appropriate permissions
- PySpark environment (for data processing)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd rules-engine-framework

# Install dependencies
pip install -r requirements.txt

# Set up database schema
psql -h <aurora-endpoint> -U <username> -d <database> -f sql/metadata_schema.sql
```

### Configuration

Copy and edit configuration file:

```bash
cp config/dev.yaml.example config/dev.yaml
# Edit config/dev.yaml with your settings
```

## Core Concepts

### Data Sources

Data sources represent connections to your data stores (S3, databases, etc.).

**Creating a Data Source**:

```python
from src.metadata.models import DataSource, SourceType
from src.metadata.repository import MetadataRepository

repo = MetadataRepository(...)

source = DataSource(
    source_name="Production S3",
    source_type=SourceType.S3,
    connection_config={
        "bucket": "my-data-bucket",
        "region": "us-east-1",
        "format": "parquet"
    },
    created_by="admin"
)

source_id = repo.create_data_source(source)
```

### Validation Rules

Rules define what to validate. They are reusable across multiple tables.

**Rule Types**:
- `single_field`: Validates one column
- `multi_field`: Validates multiple columns together
- `cross_table`: Validates across tables (future)

**Rule Categories**:
- `completeness`: Null/empty checks
- `accuracy`: Format, range, regex validation
- `consistency`: Cross-field validation
- `integrity`: Foreign key, uniqueness
- `timeliness`: Freshness checks
- `custom`: User-defined logic

**Creating a Rule**:

```python
from src.metadata.models import ValidationRule, RuleType, RuleCategory, SeverityLevel

rule = ValidationRule(
    rule_name="Email Format Check",
    rule_type=RuleType.SINGLE_FIELD,
    rule_category=RuleCategory.ACCURACY,
    severity_level=SeverityLevel.HIGH,
    rule_logic="is_email(col('email'))",
    threshold_value=5.0,  # Allow up to 5% failures
    created_by="admin"
)

rule_id = repo.create_rule(rule)
```

### Rule Expressions

Rules use expressions to define validation logic. Supported formats:

**Function Call Style**:
```
is_email(col('email'))
is_not_null(col('name'))
range_check(col('age'), min_value=18, max_value=100)
```

**SQL WHERE Clause Style**:
```
col('age') > 18 AND col('status') = 'active'
col('start_date') <= col('end_date')
```

**Built-in Functions**:
- `is_null(col)`, `is_not_null(col)`
- `is_empty(col)`, `is_not_empty(col)`
- `is_email(col)`, `is_phone(col)`
- `regex_match(col, pattern)`
- `range_check(col, min, max)`
- `length_check(col, min_length, max_length)`
- `equals(col1, col2)`, `greater_than(col1, col2)`
- `is_fresh(col, max_age_days)`
- `is_in_list(col, [value1, value2])`

### Rule Assignments

Assignments map rules to specific tables and columns.

**Creating an Assignment**:

```python
from src.metadata.models import RuleAssignment, ExecutionFrequency

assignment = RuleAssignment(
    rule_id=rule_id,
    source_id=source_id,
    schema_name="public",
    table_name="users",
    column_names=["email"],
    execution_frequency=ExecutionFrequency.BATCH,
    created_by="admin"
)

assignment_id = repo.assign_rule(assignment)
```

## Executing Validations

### Via Python API

```python
from src.rules.executor import RuleExecutor

executor = RuleExecutor(repo)
result = executor.execute_assignment(assignment_id)

print(f"Status: {result.status}")
print(f"Records checked: {result.records_checked}")
print(f"Records failed: {result.records_failed}")
```

### Via Lambda Function

```python
import boto3

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='rules-engine-rule-executor',
    Payload=json.dumps({
        'assignment_id': str(assignment_id),
        'execution_type': 'on_demand',
        'trigger_glue': False
    })
)
```

### Via API Gateway

```bash
curl -X POST https://api.example.com/api/validations/execute \
  -H "Content-Type: application/json" \
  -d '{
    "assignment_id": "uuid-here",
    "trigger_glue": false
  }'
```

## Batch Import

Import multiple rules from CSV/Excel:

```python
from src.utils.batch_import import BatchRuleImporter

importer = BatchRuleImporter(repo)

# Import from CSV
result = importer.import_from_csv('rules.csv', create_assignments=True)

print(f"Created {result['rules_created']} rules")
print(f"Created {result['assignments_created']} assignments")
```

**CSV Format**:
```csv
rule_name,rule_type,rule_category,severity_level,rule_logic,created_by,target_source,target_schema,target_table,target_columns,execution_frequency
Email Check,single_field,accuracy,high,is_email(col('email')),admin,Production S3,public,users,email,batch
Age Range,single_field,accuracy,medium,range_check(col('age'), 18, 100),admin,Production S3,public,users,age,batch
```

## Querying Results

### Get Validation Results

```python
# Get results for a rule
results = repo.get_validation_results(
    rule_id=rule_id,
    limit=100
)

# Get results for an assignment
results = repo.get_validation_results(
    assignment_id=assignment_id,
    status='fail'
)
```

### Via API

```bash
curl "https://api.example.com/api/validations/results?rule_id=uuid&status=fail&limit=100"
```

## Best Practices

1. **Reusable Rules**: Create reusable rules that can be applied to multiple tables
2. **Threshold Values**: Set appropriate thresholds based on business requirements
3. **Severity Levels**: Use severity levels to prioritize fixes
4. **Incremental Validation**: Use incremental validation for large datasets
5. **Monitoring**: Set up CloudWatch alarms for critical failures
6. **Documentation**: Document complex rule logic in the description field

## Common Patterns

### Completeness Check

```python
rule_logic = "is_not_null(col('email'))"
```

### Format Validation

```python
rule_logic = "is_email(col('email'))"
rule_logic = "regex_match(col('phone'), r'^\\d{10}$')"
```

### Range Validation

```python
rule_logic = "range_check(col('age'), min_value=18, max_value=100)"
```

### Cross-Field Validation

```python
rule_logic = "col('start_date') <= col('end_date')"
rule_logic = "col('total') == col('subtotal') + col('tax')"
```

### List Validation

```python
rule_logic = "is_in_list(col('status'), ['active', 'inactive', 'pending'])"
```

## Troubleshooting

### Connection Issues

- Verify connection configuration in `data_sources` table
- Check network connectivity and firewall rules
- Verify credentials in AWS Secrets Manager

### Rule Execution Failures

- Check rule expression syntax
- Verify column names match actual table columns
- Review execution logs in CloudWatch

### Performance Issues

- Use Glue jobs for large datasets (>1GB)
- Enable partition pruning for partitioned data
- Consider incremental validation for frequently updated tables
