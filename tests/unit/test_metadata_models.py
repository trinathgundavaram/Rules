"""Unit tests for metadata models."""

import pytest
from datetime import datetime
from uuid import uuid4

from pydantic import ValidationError

from src.metadata.models import (
    DataSource,
    ExecutionLog,
    ExecutionStatus,
    QualityScore,
    RuleAssignment,
    RuleCategory,
    RuleType,
    SeverityLevel,
    SourceType,
    ValidationResult,
    ValidationStatus,
    ValidationRule,
)


class TestDataSource:
    """Tests for DataSource model."""

    def test_create_valid_data_source(self):
        """Test creating a valid data source."""
        source = DataSource(
            source_name="Test Source",
            source_type=SourceType.S3,
            connection_config={"bucket": "test"},
            created_by="test_user",
        )
        assert source.source_name == "Test Source"
        assert source.source_type == SourceType.S3

    def test_data_source_defaults(self):
        """Test data source default values."""
        source = DataSource(
            source_name="Test",
            source_type=SourceType.S3,
            connection_config={},
            created_by="test",
        )
        assert source.is_active is True
        assert source.created_at is None  # Will be set by DB


class TestValidationRule:
    """Tests for ValidationRule model."""

    def test_create_valid_rule(self):
        """Test creating a valid rule."""
        rule = ValidationRule(
            rule_name="Test Rule",
            rule_type=RuleType.SINGLE_FIELD,
            rule_category=RuleCategory.ACCURACY,
            severity_level=SeverityLevel.HIGH,
            rule_logic="is_email(col('email'))",
            created_by="test_user",
        )
        assert rule.rule_name == "Test Rule"
        assert rule.is_reusable is True
        assert rule.version == 1

    def test_rule_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            ValidationRule(
                rule_name="Test",
                # Missing required fields
            )


class TestRuleAssignment:
    """Tests for RuleAssignment model."""

    def test_create_valid_assignment(self):
        """Test creating a valid assignment."""
        assignment = RuleAssignment(
            rule_id=uuid4(),
            source_id=uuid4(),
            schema_name="public",
            table_name="users",
            column_names=["email"],
            execution_frequency="batch",
            created_by="test",
        )
        assert assignment.schema_name == "public"
        assert len(assignment.column_names) == 1

    def test_assignment_empty_columns(self):
        """Test that empty column list raises error."""
        with pytest.raises(ValidationError):
            RuleAssignment(
                rule_id=uuid4(),
                source_id=uuid4(),
                schema_name="public",
                table_name="users",
                column_names=[],  # Empty list
                execution_frequency="batch",
                created_by="test",
            )


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_calculate_failure_rate(self):
        """Test failure rate calculation."""
        result = ValidationResult(
            rule_id=uuid4(),
            assignment_id=uuid4(),
            execution_id=uuid4(),
            records_checked=100,
            records_failed=10,
            records_passed=90,
            status=ValidationStatus.FAIL,
        )
        assert result.calculate_failure_rate() == 10.0

    def test_calculate_failure_rate_zero_checked(self):
        """Test failure rate with zero records checked."""
        result = ValidationResult(
            rule_id=uuid4(),
            assignment_id=uuid4(),
            execution_id=uuid4(),
            records_checked=0,
            records_failed=0,
            records_passed=0,
            status=ValidationStatus.PASS,
        )
        assert result.calculate_failure_rate() == 0.0


class TestExecutionLog:
    """Tests for ExecutionLog model."""

    def test_calculate_duration(self):
        """Test duration calculation."""
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 10, 5, 0)  # 5 minutes later
        
        log = ExecutionLog(
            execution_id=uuid4(),
            execution_type="batch",
            start_time=start,
            end_time=end,
            status=ExecutionStatus.COMPLETED,
        )
        
        duration_ms = log.calculate_duration_ms()
        assert duration_ms == 300000  # 5 minutes in milliseconds

    def test_calculate_duration_no_end_time(self):
        """Test duration calculation without end time."""
        log = ExecutionLog(
            execution_id=uuid4(),
            execution_type="batch",
            start_time=datetime.utcnow(),
            end_time=None,
            status=ExecutionStatus.RUNNING,
        )
        
        assert log.calculate_duration_ms() is None


class TestQualityScore:
    """Tests for QualityScore model."""

    def test_create_valid_score(self):
        """Test creating a valid quality score."""
        score = QualityScore(
            score_date=datetime.utcnow(),
            overall_score=85.5,
            completeness_score=90.0,
            accuracy_score=80.0,
        )
        assert score.overall_score == 85.5

    def test_score_range_validation(self):
        """Test that scores must be between 0 and 100."""
        with pytest.raises(ValidationError):
            QualityScore(
                score_date=datetime.utcnow(),
                overall_score=150,  # Invalid
            )
