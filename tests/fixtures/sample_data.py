"""Sample data for testing."""

from typing import Dict, List

# Sample CSV data for batch import testing
SAMPLE_RULES_CSV = """rule_name,rule_type,rule_category,severity_level,rule_logic,threshold_value,description,created_by,target_source,target_schema,target_table,target_columns,execution_frequency
Email Format Check,single_field,accuracy,high,is_email(col('email')),5.0,Validates email format,admin,Test S3 Source,public,users,email,batch
Age Range Check,single_field,accuracy,medium,range_check(col('age'), 18, 100),10.0,Validates age range,admin,Test S3 Source,public,users,age,batch
Name Completeness,single_field,completeness,high,is_not_empty(col('name')),0.0,Ensures name is not empty,admin,Test S3 Source,public,users,name,batch
"""

# Sample rule definitions
SAMPLE_RULES: List[Dict] = [
    {
        "rule_name": "Email Format Validation",
        "rule_type": "single_field",
        "rule_category": "accuracy",
        "severity_level": "high",
        "rule_logic": "is_email(col('email'))",
        "threshold_value": 5.0,
        "description": "Validates email format",
        "created_by": "admin",
    },
    {
        "rule_name": "Age Range Check",
        "rule_type": "single_field",
        "rule_category": "accuracy",
        "severity_level": "medium",
        "rule_logic": "range_check(col('age'), min_value=18, max_value=100)",
        "threshold_value": 10.0,
        "description": "Validates age is between 18 and 100",
        "created_by": "admin",
    },
    {
        "rule_name": "Name Completeness",
        "rule_type": "single_field",
        "rule_category": "completeness",
        "severity_level": "high",
        "rule_logic": "is_not_empty(col('name'))",
        "threshold_value": 0.0,
        "description": "Ensures name field is not empty",
        "created_by": "admin",
    },
]

# Sample connection configurations
SAMPLE_CONNECTION_CONFIGS: Dict[str, Dict] = {
    "s3": {
        "bucket": "test-data-bucket",
        "region": "us-east-1",
        "format": "parquet",
    },
    "databricks": {
        "server_hostname": "test.cloud.databricks.com",
        "http_path": "/sql/1.0/endpoints/abc123",
        "access_token": "dapi1234567890",
        "catalog": "hive_metastore",
        "schema": "default",
    },
    "sqlserver": {
        "server": "test-server.database.windows.net",
        "port": 1433,
        "database": "testdb",
        "username": "testuser",
        "password": "testpass",
        "schema": "dbo",
    },
}
