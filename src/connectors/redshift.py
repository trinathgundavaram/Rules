"""Redshift connector implementation."""

from typing import Any, Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql import SparkSession

from src.connectors.base import BaseConnector
from src.utils.exceptions import ConnectionError, ConnectorException
from src.utils.logger import get_logger


class RedshiftConnector(BaseConnector):
    """Connector for Amazon Redshift data sources."""

    def __init__(
        self,
        connection_config: Dict[str, Any],
        spark_session: Optional[SparkSession] = None,
    ):
        """
        Initialize Redshift connector.

        Args:
            connection_config: Must contain 'host', 'database', 'username',
                              'password', 'port', and optionally 'schema'
            spark_session: Spark session (required)
        """
        super().__init__(connection_config, spark_session)
        self.host = connection_config.get("host")
        self.port = connection_config.get("port", 5439)
        self.database = connection_config.get("database")
        self.username = connection_config.get("username")
        self.password = connection_config.get("password")
        self.schema = connection_config.get("schema", "public")
        self.s3_temp_dir = connection_config.get(
            "s3_temp_dir"
        )  # Required for Redshift writes

        if not all([self.host, self.database, self.username, self.password]):
            raise ConnectorException(
                "Redshift connection requires host, database, username, and password"
            )

        if not self.spark_session:
            raise ConnectorException("Spark session is required for Redshift connector")

    def connect(self) -> None:
        """Establish connection to Redshift."""
        try:
            self.logger.info(
                "Connecting to Redshift",
                host=self.host,
                database=self.database,
            )

            # Redshift uses PostgreSQL JDBC driver
            jdbc_url = (
                f"jdbc:redshift://{self.host}:{self.port}/{self.database}"
            )

            # Test connection
            test_df = (
                self.spark_session.read.format("jdbc")
                .option("url", jdbc_url)
                .option("dbtable", "(SELECT 1 AS test) AS t")
                .option("user", self.username)
                .option("password", self.password)
                .option("driver", "com.amazon.redshift.jdbc.Driver")
                .load()
            )
            test_df.collect()

            self._is_connected = True
            self.logger.info("Successfully connected to Redshift")

        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redshift: {str(e)}") from e

    def disconnect(self) -> None:
        """Close Redshift connection."""
        self._is_connected = False
        self.logger.info("Disconnected from Redshift")

    def _get_jdbc_url(self) -> str:
        """Get JDBC URL for Redshift."""
        return f"jdbc:redshift://{self.host}:{self.port}/{self.database}"

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
        Read data from Redshift.

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
            jdbc_url = self._get_jdbc_url()
            schema_name = schema or self.schema

            if query:
                self.logger.info("Executing SQL query on Redshift")
                df = (
                    self.spark_session.read.format("jdbc")
                    .option("url", jdbc_url)
                    .option("query", query)
                    .option("user", self.username)
                    .option("password", self.password)
                    .option("driver", "com.amazon.redshift.jdbc.Driver")
                    .load()
                )
            elif table:
                full_table_name = f"{schema_name}.{table}"
                self.logger.info("Reading table from Redshift", table=full_table_name)
                df = (
                    self.spark_session.read.format("jdbc")
                    .option("url", jdbc_url)
                    .option("dbtable", full_table_name)
                    .option("user", self.username)
                    .option("password", self.password)
                    .option("driver", "com.amazon.redshift.jdbc.Driver")
                    .load()
                )
            else:
                raise ConnectorException("Either query or table must be provided")

            df = self._apply_filters(df, filters)
            df = self._select_columns(df, columns)

            if limit:
                df = df.limit(limit)

            return df

        except Exception as e:
            raise ConnectorException(
                f"Failed to read data from Redshift: {str(e)}"
            ) from e

    def write_results(
        self,
        data: DataFrame,
        destination: str,
        mode: str = "overwrite",
        partition_by: Optional[List[str]] = None,
    ) -> None:
        """
        Write results to Redshift table.

        Args:
            data: DataFrame to write
            destination: Table name (can include schema.table)
            mode: Write mode
            partition_by: Columns to partition by (uses S3 staging)
        """
        self._validate_connection()

        if not self.s3_temp_dir:
            raise ConnectorException(
                "S3 temporary directory is required for Redshift writes"
            )

        self.logger.info("Writing data to Redshift", destination=destination, mode=mode)

        try:
            jdbc_url = self._get_jdbc_url()

            writer = (
                data.write.format("jdbc")
                .mode(mode)
                .option("url", jdbc_url)
                .option("dbtable", destination)
                .option("user", self.username)
                .option("password", self.password)
                .option("driver", "com.amazon.redshift.jdbc.Driver")
                .option("tempdir", self.s3_temp_dir)
            )

            if partition_by:
                writer = writer.option("distkey", partition_by[0])

            writer.save()

            self.logger.info("Successfully wrote data to Redshift")

        except Exception as e:
            raise ConnectorException(
                f"Failed to write data to Redshift: {str(e)}"
            ) from e

    def get_schema(
        self,
        table: str,
        schema: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get schema for Redshift table.

        Args:
            table: Table name
            schema: Schema name (defaults to configured schema)

        Returns:
            Dictionary mapping column names to data types
        """
        self._validate_connection()

        schema_name = schema or self.schema
        full_table_name = f"{schema_name}.{table}"

        try:
            jdbc_url = self._get_jdbc_url()
            df = (
                self.spark_session.read.format("jdbc")
                .option("url", jdbc_url)
                .option("dbtable", full_table_name)
                .option("user", self.username)
                .option("password", self.password)
                .option("driver", "com.amazon.redshift.jdbc.Driver")
                .load()
                .limit(0)
            )

            schema_dict = {
                field.name: field.dataType.simpleString()
                for field in df.schema.fields
            }
            return schema_dict

        except Exception as e:
            raise ConnectorException(
                f"Failed to get schema from Redshift: {str(e)}"
            ) from e

    def test_connection(self) -> bool:
        """
        Test Redshift connection.

        Returns:
            True if connection successful
        """
        try:
            if not self._is_connected:
                self.connect()
            jdbc_url = self._get_jdbc_url()
            test_df = (
                self.spark_session.read.format("jdbc")
                .option("url", jdbc_url)
                .option("dbtable", "(SELECT 1 AS test) AS t")
                .option("user", self.username)
                .option("password", self.password)
                .option("driver", "com.amazon.redshift.jdbc.Driver")
                .load()
            )
            test_df.collect()
            return True
        except Exception as e:
            self.logger.error("Redshift connection test failed", error=str(e))
            return False
