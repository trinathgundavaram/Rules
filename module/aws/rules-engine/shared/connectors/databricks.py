"""Databricks connector implementation."""

from typing import Any, Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql import SparkSession

from connectors.base import BaseConnector
from utils.exceptions import ConnectionError, ConnectorException
from utils.logger import get_logger


class DatabricksConnector(BaseConnector):
    """Connector for Databricks data sources."""

    def __init__(
        self,
        connection_config: Dict[str, Any],
        spark_session: Optional[SparkSession] = None,
    ):
        """
        Initialize Databricks connector.

        Args:
            connection_config: Must contain 'server_hostname', 'http_path',
                              'access_token', and optionally 'catalog', 'schema'
            spark_session: Spark session (required)
        """
        super().__init__(connection_config, spark_session)
        self.server_hostname = connection_config.get("server_hostname")
        self.http_path = connection_config.get("http_path")
        self.access_token = connection_config.get("access_token")
        self.catalog = connection_config.get("catalog", "hive_metastore")
        self.schema = connection_config.get("schema", "default")

        if not all([self.server_hostname, self.http_path, self.access_token]):
            raise ConnectorException(
                "Databricks connection requires server_hostname, http_path, and access_token"
            )

        if not self.spark_session:
            raise ConnectorException("Spark session is required for Databricks connector")

    def connect(self) -> None:
        """Establish connection to Databricks."""
        try:
            self.logger.info(
                "Connecting to Databricks",
                server=self.server_hostname,
                catalog=self.catalog,
            )

            # Configure Spark for Databricks
            spark_conf = self.spark_session.conf
            spark_conf.set(
                "spark.databricks.service.address",
                f"https://{self.server_hostname}",
            )
            spark_conf.set("spark.databricks.service.token", self.access_token)

            # Test connection with a simple query
            test_df = self.spark_session.sql("SELECT 1")
            test_df.collect()

            self._is_connected = True
            self.logger.info("Successfully connected to Databricks")

        except Exception as e:
            raise ConnectionError(f"Failed to connect to Databricks: {str(e)}") from e

    def disconnect(self) -> None:
        """Close Databricks connection."""
        self._is_connected = False
        self.logger.info("Disconnected from Databricks")

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
        Read data from Databricks.

        Args:
            query: SQL query (preferred method)
            table: Table name (used with schema)
            schema: Schema name (defaults to configured schema)
            filters: Pushdown filters
            columns: Columns to select
            limit: Maximum rows to return

        Returns:
            PySpark DataFrame
        """
        self._validate_connection()

        try:
            if query:
                self.logger.info("Executing SQL query on Databricks")
                df = self.spark_session.sql(query)
            elif table:
                schema_name = schema or self.schema
                full_table_name = f"{self.catalog}.{schema_name}.{table}"
                self.logger.info("Reading table from Databricks", table=full_table_name)
                df = self.spark_session.table(full_table_name)
            else:
                raise ConnectorException("Either query or table must be provided")

            # Apply filters
            df = self._apply_filters(df, filters)

            # Select columns
            df = self._select_columns(df, columns)

            # Apply limit
            if limit:
                df = df.limit(limit)

            return df

        except Exception as e:
            raise ConnectorException(
                f"Failed to read data from Databricks: {str(e)}"
            ) from e

    def write_results(
        self,
        data: DataFrame,
        destination: str,
        mode: str = "overwrite",
        partition_by: Optional[List[str]] = None,
    ) -> None:
        """
        Write results to Databricks table.

        Args:
            data: DataFrame to write
            destination: Table name (can include catalog.schema.table)
            mode: Write mode
            partition_by: Columns to partition by
        """
        self._validate_connection()

        self.logger.info("Writing data to Databricks", destination=destination, mode=mode)

        try:
            writer = data.write.mode(mode)

            if partition_by:
                writer = writer.partitionBy(*partition_by)

            writer.saveAsTable(destination)

            self.logger.info("Successfully wrote data to Databricks")

        except Exception as e:
            raise ConnectorException(
                f"Failed to write data to Databricks: {str(e)}"
            ) from e

    def get_schema(
        self,
        table: str,
        schema: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get schema for Databricks table.

        Args:
            table: Table name
            schema: Schema name (defaults to configured schema)

        Returns:
            Dictionary mapping column names to data types
        """
        self._validate_connection()

        schema_name = schema or self.schema
        full_table_name = f"{self.catalog}.{schema_name}.{table}"

        try:
            df = self.spark_session.table(full_table_name).limit(0)
            schema_dict = {
                field.name: field.dataType.simpleString()
                for field in df.schema.fields
            }
            return schema_dict

        except Exception as e:
            raise ConnectorException(
                f"Failed to get schema from Databricks: {str(e)}"
            ) from e

    def test_connection(self) -> bool:
        """
        Test Databricks connection.

        Returns:
            True if connection successful
        """
        try:
            if not self._is_connected:
                self.connect()
            test_df = self.spark_session.sql("SELECT 1")
            test_df.collect()
            return True
        except Exception as e:
            self.logger.error("Databricks connection test failed", error=str(e))
            return False
