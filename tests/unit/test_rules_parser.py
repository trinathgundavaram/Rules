"""Unit tests for rule parser."""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

from src.rules.parser import RuleParser, parse_rule_expression
from src.utils.exceptions import RuleParseException


class TestRuleParser:
    """Tests for RuleParser."""

    def test_parse_column_reference(self):
        """Test parsing simple column reference."""
        parser = RuleParser()
        result = parser.parse("email")
        assert result is not None

    def test_parse_function_call(self):
        """Test parsing function call."""
        parser = RuleParser()
        result = parser.parse("is_email(col('email'))")
        assert result is not None

    def test_parse_sql_style(self):
        """Test parsing SQL-style expression."""
        parser = RuleParser()
        result = parser.parse("col('age') > 18 AND col('status') = 'active'")
        assert result is not None

    def test_parse_with_column_mapping(self):
        """Test parsing with column mapping."""
        parser = RuleParser()
        column_mapping = {"email_col": "user_email"}
        result = parser.parse("is_email(col('email_col'))", column_mapping)
        assert result is not None

    def test_parse_invalid_expression(self):
        """Test parsing invalid expression raises error."""
        parser = RuleParser()
        with pytest.raises(RuleParseException):
            parser.parse("invalid syntax !@#$%")

    def test_parse_convenience_function(self):
        """Test parse_rule_expression convenience function."""
        result = parse_rule_expression("is_not_null(col('name'))")
        assert result is not None


class TestRuleParserWithDataFrame:
    """Tests for RuleParser with actual DataFrames."""

    def test_apply_parsed_rule(self, spark_session, sample_spark_dataframe):
        """Test applying parsed rule to DataFrame."""
        parser = RuleParser()
        rule_expr = parser.parse("is_email(col('email'))")
        
        # Apply rule
        df_with_validation = sample_spark_dataframe.withColumn(
            "_is_valid_email", rule_expr
        )
        
        # Check results
        valid_count = df_with_validation.filter("_is_valid_email = true").count()
        assert valid_count == 2  # Two valid emails in sample data

    def test_range_check_rule(self, spark_session, sample_spark_dataframe):
        """Test range check rule."""
        parser = RuleParser()
        rule_expr = parser.parse("range_check(col('age'), min_value=18, max_value=100)")
        
        df_with_validation = sample_spark_dataframe.withColumn(
            "_age_valid", rule_expr
        )
        
        valid_count = df_with_validation.filter("_age_valid = true").count()
        assert valid_count == 4  # All ages in sample are valid
