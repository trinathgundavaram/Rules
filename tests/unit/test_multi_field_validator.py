"""Unit tests for multi-field validator."""

import pytest
from uuid import uuid4

from src.metadata.models import RuleCategory, RuleType, SeverityLevel, ValidationRule
from src.rules.multi_field import MultiFieldValidator


class TestMultiFieldValidator:
    """Tests for MultiFieldValidator."""

    def test_validate_consistency_equals(self, spark_session):
        """Test consistency validation with equals."""
        validator = MultiFieldValidator()
        data = [
            ("A", "A"),
            ("B", "B"),
            ("C", "D"),  # Not equal
        ]
        df = spark_session.createDataFrame(data, ["col1", "col2"])
        
        result = validator.validate_consistency(df, "col1", "col2", relationship="equals")
        
        assert result["records_checked"] == 3
        assert result["records_failed"] == 1  # One pair not equal

    def test_validate_consistency_greater_than(self, spark_session):
        """Test consistency validation with greater_than."""
        validator = MultiFieldValidator()
        data = [
            (10, 5),   # 10 > 5
            (20, 15),  # 20 > 15
            (5, 10),   # 5 < 10 (should fail)
        ]
        df = spark_session.createDataFrame(data, ["start", "end"])
        
        result = validator.validate_consistency(
            df, "start", "end", relationship="greater_than"
        )
        
        assert result["records_checked"] == 3
        assert result["records_failed"] == 1

    def test_validate_business_logic(self, spark_session):
        """Test business logic validation."""
        validator = MultiFieldValidator()
        data = [
            (100, 50, 50),   # total = subtotal + tax
            (200, 150, 50),  # total = subtotal + tax
            (100, 80, 30),   # total != subtotal + tax (should fail)
        ]
        df = spark_session.createDataFrame(data, ["total", "subtotal", "tax"])
        
        rule_logic = "col('total') == col('subtotal') + col('tax')"
        result = validator.validate_business_logic(
            df, rule_logic, ["total", "subtotal", "tax"]
        )
        
        assert result["records_checked"] == 3
        assert result["records_failed"] == 1

    def test_validate_with_rule(self, spark_session):
        """Test validation with a rule object."""
        validator = MultiFieldValidator()
        data = [
            ("2024-01-01", "2024-01-02"),
            ("2024-01-01", "2024-01-01"),
            ("2024-01-02", "2024-01-01"),  # start > end (should fail)
        ]
        df = spark_session.createDataFrame(data, ["start_date", "end_date"])
        
        rule = ValidationRule(
            rule_id=uuid4(),
            rule_name="Date Range Check",
            rule_type=RuleType.MULTI_FIELD,
            rule_category=RuleCategory.CONSISTENCY,
            severity_level=SeverityLevel.HIGH,
            rule_logic="col('start_date') <= col('end_date')",
            created_by="test",
        )
        
        result = validator.validate(df, rule, ["start_date", "end_date"])
        
        assert result["records_checked"] == 3
        assert result["records_failed"] == 1
