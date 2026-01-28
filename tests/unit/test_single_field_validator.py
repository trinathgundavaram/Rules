"""Unit tests for single-field validator."""

import pytest
from uuid import uuid4

from src.metadata.models import RuleCategory, RuleType, SeverityLevel, ValidationRule
from src.rules.single_field import SingleFieldValidator
from src.utils.exceptions import RuleExecutionException


class TestSingleFieldValidator:
    """Tests for SingleFieldValidator."""

    def test_validate_completeness(self, sample_spark_dataframe):
        """Test completeness validation."""
        validator = SingleFieldValidator()
        result = validator.validate_completeness(
            sample_spark_dataframe, "email", allow_empty_strings=False
        )
        
        assert result["records_checked"] == 4
        assert result["records_failed"] == 1  # One null email
        assert result["status"] in ["pass", "fail"]

    def test_validate_accuracy_email(self, sample_spark_dataframe):
        """Test email accuracy validation."""
        validator = SingleFieldValidator()
        result = validator.validate_accuracy(
            sample_spark_dataframe, "email", validation_type="email"
        )
        
        assert result["records_checked"] == 4
        assert result["records_failed"] == 2  # invalid-email and null
        assert "sample_failed_records" in result

    def test_validate_accuracy_range(self, sample_spark_dataframe):
        """Test range accuracy validation."""
        validator = SingleFieldValidator()
        result = validator.validate_accuracy(
            sample_spark_dataframe,
            "age",
            validation_type="range",
            min_value=18,
            max_value=100,
        )
        
        assert result["records_checked"] == 4
        assert result["status"] in ["pass", "fail"]

    def test_validate_with_rule(self, sample_spark_dataframe):
        """Test validation with a rule object."""
        validator = SingleFieldValidator()
        rule = ValidationRule(
            rule_id=uuid4(),
            rule_name="Test Rule",
            rule_type=RuleType.SINGLE_FIELD,
            rule_category=RuleCategory.ACCURACY,
            severity_level=SeverityLevel.HIGH,
            rule_logic="is_email(col('email'))",
            created_by="test",
        )
        
        result = validator.validate(sample_spark_dataframe, rule, "email")
        
        assert result["records_checked"] == 4
        assert "records_failed" in result
        assert "failure_rate" in result
        assert "sample_failed_records" in result

    def test_validate_with_threshold(self, sample_spark_dataframe):
        """Test validation with threshold."""
        validator = SingleFieldValidator()
        rule = ValidationRule(
            rule_id=uuid4(),
            rule_name="Test Rule",
            rule_type=RuleType.SINGLE_FIELD,
            rule_category=RuleCategory.ACCURACY,
            severity_level=SeverityLevel.HIGH,
            rule_logic="is_email(col('email'))",
            threshold_value=50.0,  # Allow up to 50% failures
            created_by="test",
        )
        
        result = validator.validate(sample_spark_dataframe, rule, "email")
        
        # With 50% threshold, 2 failures out of 4 should pass
        assert result["failure_rate"] == 50.0
        assert result["status"] == "pass"  # Should pass with 50% threshold

    def test_validate_invalid_rule_logic(self, sample_spark_dataframe):
        """Test validation with invalid rule logic raises error."""
        validator = SingleFieldValidator()
        rule = ValidationRule(
            rule_id=uuid4(),
            rule_name="Test Rule",
            rule_type=RuleType.SINGLE_FIELD,
            rule_category=RuleCategory.ACCURACY,
            severity_level=SeverityLevel.HIGH,
            rule_logic="invalid_syntax !@#$",
            created_by="test",
        )
        
        with pytest.raises(RuleExecutionException):
            validator.validate(sample_spark_dataframe, rule, "email")
