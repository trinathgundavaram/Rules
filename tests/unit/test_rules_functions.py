"""Unit tests for rule functions."""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

from src.rules.functions import RuleFunctions, FUNCTION_REGISTRY


class TestRuleFunctions:
    """Tests for RuleFunctions."""

    def test_is_null(self, spark_session, sample_spark_dataframe):
        """Test is_null function."""
        result = RuleFunctions.is_null(col("email"))
        df_with_check = sample_spark_dataframe.withColumn("_is_null", result)
        null_count = df_with_check.filter("_is_null = true").count()
        assert null_count == 1  # One null email in sample data

    def test_is_not_null(self, spark_session, sample_spark_dataframe):
        """Test is_not_null function."""
        result = RuleFunctions.is_not_null(col("email"))
        df_with_check = sample_spark_dataframe.withColumn("_is_not_null", result)
        not_null_count = df_with_check.filter("_is_not_null = true").count()
        assert not_null_count == 3  # Three non-null emails

    def test_is_empty(self, spark_session):
        """Test is_empty function."""
        data = [("",), ("  ",), ("value",), (None,)]
        df = spark_session.createDataFrame(data, ["col1"])
        result = RuleFunctions.is_empty(col("col1"))
        df_with_check = df.withColumn("_is_empty", result)
        empty_count = df_with_check.filter("_is_empty = true").count()
        assert empty_count == 3  # Empty string, whitespace, and null

    def test_is_email(self, spark_session):
        """Test is_email function."""
        data = [
            ("valid@example.com",),
            ("invalid-email",),
            ("another@test.co.uk",),
            ("not.an.email",),
        ]
        df = spark_session.createDataFrame(data, ["email"])
        result = RuleFunctions.is_email(col("email"))
        df_with_check = df.withColumn("_is_email", result)
        valid_count = df_with_check.filter("_is_email = true").count()
        assert valid_count == 2  # Two valid emails

    def test_range_check(self, spark_session):
        """Test range_check function."""
        data = [(10,), (25,), (50,), (100,), (150,)]
        df = spark_session.createDataFrame(data, ["value"])
        result = RuleFunctions.range_check(col("value"), min_value=20, max_value=100)
        df_with_check = df.withColumn("_in_range", result)
        valid_count = df_with_check.filter("_in_range = true").count()
        assert valid_count == 3  # 25, 50, 100 are in range

    def test_length_check(self, spark_session):
        """Test length_check function."""
        data = [("short",), ("medium length",), ("very long string here",)]
        df = spark_session.createDataFrame(data, ["text"])
        result = RuleFunctions.length_check(col("text"), min_length=5, max_length=15)
        df_with_check = df.withColumn("_valid_length", result)
        valid_count = df_with_check.filter("_valid_length = true").count()
        assert valid_count == 2  # "short" and "medium length"

    def test_is_in_list(self, spark_session):
        """Test is_in_list function."""
        data = [("active",), ("inactive",), ("pending",), ("unknown",)]
        df = spark_session.createDataFrame(data, ["status"])
        result = RuleFunctions.is_in_list(col("status"), ["active", "inactive", "pending"])
        df_with_check = df.withColumn("_in_list", result)
        valid_count = df_with_check.filter("_in_list = true").count()
        assert valid_count == 3  # active, inactive, pending

    def test_equals(self, spark_session):
        """Test equals function."""
        data = [(10, 10), (10, 20), (30, 30)]
        df = spark_session.createDataFrame(data, ["col1", "col2"])
        result = RuleFunctions.equals(col("col1"), col("col2"))
        df_with_check = df.withColumn("_equals", result)
        equal_count = df_with_check.filter("_equals = true").count()
        assert equal_count == 2  # Two pairs are equal

    def test_function_registry(self):
        """Test that all functions are registered."""
        assert "is_email" in FUNCTION_REGISTRY
        assert "is_null" in FUNCTION_REGISTRY
        assert "range_check" in FUNCTION_REGISTRY
        assert len(FUNCTION_REGISTRY) > 10  # Should have many functions
