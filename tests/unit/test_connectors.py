"""Unit tests for data connectors."""

import pytest
from pyspark.sql import SparkSession
from unittest.mock import Mock, patch, MagicMock

from src.connectors.base import BaseConnector
from src.connectors.factory import ConnectorFactory
from src.connectors.s3 import S3Connector
from src.utils.exceptions import ConnectorException, ConfigurationException


class TestConnectorFactory:
    """Tests for ConnectorFactory."""

    def test_create_s3_connector(self, spark_session):
        """Test creating S3 connector."""
        config = {
            "bucket": "test-bucket",
            "region": "us-east-1",
            "format": "parquet",
        }
        connector = ConnectorFactory.create_connector(
            "s3", config, spark_session
        )
        assert isinstance(connector, S3Connector)
        assert connector.bucket == "test-bucket"

    def test_create_unsupported_connector(self):
        """Test creating unsupported connector raises error."""
        with pytest.raises(ConfigurationException):
            ConnectorFactory.create_connector("unsupported", {})

    def test_register_custom_connector(self, spark_session):
        """Test registering a custom connector."""
        class CustomConnector(BaseConnector):
            def connect(self): pass
            def disconnect(self): pass
            def read_data(self, **kwargs): pass
            def write_results(self, **kwargs): pass
            def get_schema(self, **kwargs): pass
            def test_connection(self): return True

        ConnectorFactory.register_connector("custom", CustomConnector)
        connector = ConnectorFactory.create_connector("custom", {}, spark_session)
        assert isinstance(connector, CustomConnector)


class TestS3Connector:
    """Tests for S3Connector."""

    def test_init_missing_bucket(self, spark_session):
        """Test initialization without bucket raises error."""
        with pytest.raises(ConnectorException):
            S3Connector({}, spark_session)

    def test_init_missing_spark(self):
        """Test initialization without Spark session raises error."""
        config = {"bucket": "test-bucket"}
        with pytest.raises(ConnectorException):
            S3Connector(config, None)

    def test_context_manager(self, spark_session):
        """Test connector as context manager."""
        config = {
            "bucket": "test-bucket",
            "region": "us-east-1",
            "format": "parquet",
        }
        connector = S3Connector(config, spark_session)
        
        with patch.object(connector, 'connect') as mock_connect, \
             patch.object(connector, 'disconnect') as mock_disconnect:
            with connector:
                mock_connect.assert_called_once()
            mock_disconnect.assert_called_once()

    def test_apply_filters(self, spark_session, sample_spark_dataframe):
        """Test filter application."""
        config = {
            "bucket": "test-bucket",
            "region": "us-east-1",
            "format": "parquet",
        }
        connector = S3Connector(config, spark_session)
        
        filters = {"age": {"gte": 30}}
        result = connector._apply_filters(sample_spark_dataframe, filters)
        assert result.count() == 2  # Should filter to age >= 30

    def test_select_columns(self, spark_session, sample_spark_dataframe):
        """Test column selection."""
        config = {
            "bucket": "test-bucket",
            "region": "us-east-1",
            "format": "parquet",
        }
        connector = S3Connector(config, spark_session)
        
        result = connector._select_columns(sample_spark_dataframe, ["email", "name"])
        assert len(result.columns) == 2
        assert "email" in result.columns
        assert "name" in result.columns
