"""Pytest configuration and fixtures."""

import os
from typing import Generator
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
from pyspark.sql import SparkSession

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


@pytest.fixture(scope="session")
def spark_session() -> Generator[SparkSession, None, None]:
    """Create a Spark session for testing."""
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("rules-engine-test")
        .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse")
        .getOrCreate()
    )
    yield spark
    spark.stop()


@pytest.fixture
def mock_metadata_repo() -> MagicMock:
    """Create a mock metadata repository."""
    repo = MagicMock(spec=MetadataRepository)
    return repo


@pytest.fixture
def sample_data_source() -> DataSource:
    """Create a sample data source for testing."""
    return DataSource(
        source_id=uuid4(),
        source_name="Test S3 Source",
        source_type=SourceType.S3,
        connection_config={
            "bucket": "test-bucket",
            "region": "us-east-1",
            "format": "parquet",
        },
        is_active=True,
        created_by="test_user",
    )


@pytest.fixture
def sample_rule() -> ValidationRule:
    """Create a sample validation rule for testing."""
    return ValidationRule(
        rule_id=uuid4(),
        rule_name="Test Email Rule",
        rule_type=RuleType.SINGLE_FIELD,
        rule_category=RuleCategory.ACCURACY,
        severity_level=SeverityLevel.HIGH,
        rule_logic="is_email(col('email'))",
        threshold_value=5.0,
        is_reusable=True,
        created_by="test_user",
    )


@pytest.fixture
def sample_assignment(sample_rule, sample_data_source) -> RuleAssignment:
    """Create a sample rule assignment for testing."""
    return RuleAssignment(
        assignment_id=uuid4(),
        rule_id=sample_rule.rule_id,
        source_id=sample_data_source.source_id,
        schema_name="public",
        table_name="users",
        column_names=["email"],
        execution_frequency="batch",
        is_active=True,
        created_by="test_user",
    )


@pytest.fixture
def sample_spark_dataframe(spark_session):
    """Create a sample Spark DataFrame for testing."""
    data = [
        ("user1@example.com", "John Doe", 25),
        ("user2@example.com", "Jane Smith", 30),
        ("invalid-email", "Bob Johnson", 35),
        (None, "Alice Brown", 28),
    ]
    columns = ["email", "name", "age"]
    return spark_session.createDataFrame(data, columns)


@pytest.fixture
def mock_connector():
    """Create a mock connector."""
    connector = MagicMock()
    connector.connect = Mock()
    connector.disconnect = Mock()
    connector.is_connected.return_value = True
    return connector


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    # Save original values
    original_env = os.environ.copy()
    yield
    # Restore original values
    os.environ.clear()
    os.environ.update(original_env)
