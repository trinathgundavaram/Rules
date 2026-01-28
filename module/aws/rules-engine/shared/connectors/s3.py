"""S3 connector implementation."""

import json
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from pyspark.sql import DataFrame
from pyspark.sql import SparkSession

from connectors.base import BaseConnector
from utils.exceptions import ConnectionError, ConnectorException
from utils.logger import get_logger


class S3Connector(BaseConnector):
    """Connector for Amazon S3 data sources."""

    def __init__(
        self,
        connection_config: Dict[str, Any],
        spark_session: Optional[SparkSession] = None,
    ):
        """
        Initialize S3 connector.

        Args:
            connection_config: Must contain 'bucket', 'region', and optionally
                              'access_key_id', 'secret_access_key', 'format'
            spark_session: Spark session (required for S3)
        """
        super().__init__(connection_config, spark_session)
        self.bucket = connection_config.get("bucket")
        self.region = connection_config.get("region", "us-east-1")
        self.format = connection_config.get("format", "parquet")  # parquet, csv, json
        self.access_key_id = connection_config.get("access_key_id")
        self.secret_access_key = connection_config.get("secret_access_key")
        self.s3_client = None

        if not self.bucket:
            raise ConnectorException("S3 bucket name is required in connection_config")

        if not self.spark_session:
            raise ConnectorException("Spark session is required for S3 connector")

    def connect(self) -> None:
        """Establish connection to S3."""
        try:
            self.logger.info("Connecting to S3", bucket=self.bucket, region=self.region)

            # Initialize S3 client
            s3_config = {"region_name": self.region}
            if self.access_key_id and self.secret_access_key:
                s3_config["aws_access_key_id"] = self.access_key_id
                s3_config["aws_secret_access_key"] = self.secret_access_key

            self.s3_client = boto3.client("s3", **s3_config)

            # Test connection by listing bucket
            self.s3_client.head_bucket(Bucket=self.bucket)
            self._is_connected = True

            self.logger.info("Successfully connected to S3", bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            raise ConnectionError(
                f"Failed to connect to S3 bucket {self.bucket}: {error_code}"
            ) from e

    def disconnect(self) -> None:
        """Close S3 connection."""
        self.s3_client = None
        self._is_connected = False
        self.logger.info("Disconnected from S3")

    def read_data(
        self,
        query: Optional[str] = None,
        table: Optional[str] = None,
        schema: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> DataFrame:
        """
        Read data from S3.

        Args:
            query: Not used for S3 (use table parameter instead)
            table: S3 path/key (relative to bucket root)
            schema: Not used for S3
            filters: Pushdown filters (if supported by format)
            columns: Columns to select
            limit: Maximum rows to return

        Returns:
            PySpark DataFrame
        """
        self._validate_connection()

        if not table:
            raise ConnectorException("S3 path (table parameter) is required")

        s3_path = f"s3a://{self.bucket}/{table.lstrip('/')}"

        self.logger.info("Reading data from S3", path=s3_path, format=self.format)

        try:
            # Read based on format
            reader = self.spark_session.read

            if self.format == "parquet":
                df = reader.parquet(s3_path)
            elif self.format == "csv":
                df = reader.csv(
                    s3_path,
                    header=True,
                    inferSchema=True,
                )
            elif self.format == "json":
                df = reader.json(s3_path)
            else:
                raise ConnectorException(f"Unsupported S3 format: {self.format}")

            # Apply filters
            df = self._apply_filters(df, filters)

            # Select columns
            df = self._select_columns(df, columns)

            # Apply limit
            if limit:
                df = df.limit(limit)

            self.logger.info("Successfully read data from S3", row_count=df.count())
            return df

        except Exception as e:
            raise ConnectorException(f"Failed to read data from S3: {str(e)}") from e

    def write_results(
        self,
        data: DataFrame,
        destination: str,
        mode: str = "overwrite",
        partition_by: Optional[List[str]] = None,
    ) -> None:
        """
        Write results to S3.

        Args:
            data: DataFrame to write
            destination: S3 path/key (relative to bucket root)
            mode: Write mode
            partition_by: Columns to partition by
        """
        self._validate_connection()

        s3_path = f"s3a://{self.bucket}/{destination.lstrip('/')}"

        self.logger.info("Writing data to S3", path=s3_path, mode=mode)

        try:
            writer = data.write.mode(mode)

            if partition_by:
                writer = writer.partitionBy(*partition_by)

            if self.format == "parquet":
                writer.parquet(s3_path)
            elif self.format == "csv":
                writer.csv(s3_path, header=True)
            elif self.format == "json":
                writer.json(s3_path)
            else:
                raise ConnectorException(f"Unsupported S3 format: {self.format}")

            self.logger.info("Successfully wrote data to S3", path=s3_path)

        except Exception as e:
            raise ConnectorException(f"Failed to write data to S3: {str(e)}") from e

    def get_schema(
        self,
        table: str,
        schema: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get schema for S3 data.

        Args:
            table: S3 path/key
            schema: Not used for S3

        Returns:
            Dictionary mapping column names to data types
        """
        self._validate_connection()

        s3_path = f"s3a://{self.bucket}/{table.lstrip('/')}"

        try:
            # Read a sample to infer schema
            reader = self.spark_session.read

            if self.format == "parquet":
                df = reader.parquet(s3_path).limit(0)
            elif self.format == "csv":
                df = reader.csv(s3_path, header=True, inferSchema=True).limit(0)
            elif self.format == "json":
                df = reader.json(s3_path).limit(0)
            else:
                raise ConnectorException(f"Unsupported S3 format: {self.format}")

            schema_dict = {
                field.name: field.dataType.simpleString()
                for field in df.schema.fields
            }

            return schema_dict

        except Exception as e:
            raise ConnectorException(
                f"Failed to get schema from S3: {str(e)}"
            ) from e

    def test_connection(self) -> bool:
        """
        Test S3 connection.

        Returns:
            True if connection successful
        """
        try:
            if not self._is_connected:
                self.connect()
            self.s3_client.head_bucket(Bucket=self.bucket)
            return True
        except Exception as e:
            self.logger.error("S3 connection test failed", error=str(e))
            return False
