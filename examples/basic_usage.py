"""Basic usage examples for Rules Engine Framework."""

from uuid import UUID

from src.connectors.factory import ConnectorFactory
from src.metadata.models import (
    DataSource,
    RuleAssignment,
    RuleCategory,
    RuleType,
    SeverityLevel,
    SourceType,
    ValidationRule,
)
from src.metadata.repository import MetadataRepository
from src.rules.executor import RuleExecutor
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def example_create_data_source():
    """Example: Create a data source."""
    # Initialize repository
    repo = MetadataRepository(
        host="localhost",
        port=5432,
        database="rules_engine",
        username="postgres",
        password="postgres",
    )

    # Create S3 data source
    s3_source = DataSource(
        source_name="My S3 Bucket",
        source_type=SourceType.S3,
        connection_config={
            "bucket": "my-data-bucket",
            "region": "us-east-1",
            "format": "parquet",
        },
        created_by="admin",
        description="Main data bucket",
    )

    source_id = repo.create_data_source(s3_source)
    logger.info("Created data source", source_id=str(source_id))
    return source_id


def example_create_rule():
    """Example: Create a validation rule."""
    repo = MetadataRepository(
        host="localhost",
        port=5432,
        database="rules_engine",
        username="postgres",
        password="postgres",
    )

    # Create email validation rule
    email_rule = ValidationRule(
        rule_name="Email Format Validation",
        rule_type=RuleType.SINGLE_FIELD,
        rule_category=RuleCategory.ACCURACY,
        severity_level=SeverityLevel.HIGH,
        rule_logic="is_email(col('email'))",
        threshold_value=5.0,  # Allow up to 5% failures
        is_reusable=True,
        description="Validates email format using regex",
        created_by="admin",
    )

    rule_id = repo.create_rule(email_rule)
    logger.info("Created rule", rule_id=str(rule_id))
    return rule_id


def example_assign_rule():
    """Example: Assign a rule to a table."""
    repo = MetadataRepository(
        host="localhost",
        port=5432,
        database="rules_engine",
        username="postgres",
        password="postgres",
    )

    # Get rule and source IDs (from previous examples)
    rule_id = UUID("...")  # Replace with actual rule ID
    source_id = UUID("...")  # Replace with actual source ID

    # Create assignment
    assignment = RuleAssignment(
        rule_id=rule_id,
        source_id=source_id,
        schema_name="public",
        table_name="users",
        column_names=["email"],
        execution_frequency="batch",
        created_by="admin",
    )

    assignment_id = repo.assign_rule(assignment)
    logger.info("Created assignment", assignment_id=str(assignment_id))
    return assignment_id


def example_execute_validation():
    """Example: Execute a validation."""
    repo = MetadataRepository(
        host="localhost",
        port=5432,
        database="rules_engine",
        username="postgres",
        password="postgres",
    )

    executor = RuleExecutor(repo)

    # Execute validation for an assignment
    assignment_id = UUID("...")  # Replace with actual assignment ID
    result = executor.execute_assignment(assignment_id)

    logger.info(
        "Validation completed",
        result_id=str(result.result_id),
        status=result.status.value,
        records_checked=result.records_checked,
        records_failed=result.records_failed,
    )

    return result


def example_use_connector():
    """Example: Use a data connector directly."""
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.appName("Example").getOrCreate()

    # Create S3 connector
    connector = ConnectorFactory.create_connector(
        source_type="s3",
        connection_config={
            "bucket": "my-data-bucket",
            "region": "us-east-1",
            "format": "parquet",
        },
        spark_session=spark,
    )

    # Read data
    with connector:
        connector.connect()
        df = connector.read_data(
            table="users/partition=2024-01-01",
            columns=["email", "name", "age"],
            limit=1000,
        )

        # Process data
        print(f"Read {df.count()} records")
        df.show(10)


if __name__ == "__main__":
    # Run examples
    print("Creating data source...")
    source_id = example_create_data_source()

    print("Creating rule...")
    rule_id = example_create_rule()

    print("Assigning rule...")
    assignment_id = example_assign_rule()

    print("Executing validation...")
    result = example_execute_validation()

    print("Done!")
