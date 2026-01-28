"""Teradata connector implementation."""

from typing import Any, Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql import SparkSession

from connectors.base import BaseConnector
from utils.exceptions import ConnectionError, ConnectorException
from utils.logger import get_logger


class TeradataConnector(BaseConnector):
    """Connector for Teradata data sources."""

    def __init__(
        self,
        connection_config: Dict[str, Any],
        spark_session: Optional[SparkSession] = None,
    ):
        """
        Initialize Teradata connector.

        Args:
            connection_config: Must contain 'host', 'database', 'username',
                              'password', and optionally 'port', 'logmech'
            spark_session: Spark session (required)
        """
        super().__init__(connection_config, spark_session)
        self.host = connection_config.get("host")
        self.port = connection_config.get("port", 1025)
        self.database = connection_config.get("database")
        self.username = connection_config.get("username")
        self.password = connection_config.get("password")
        self.logmech = connection_config.get("logmech", "LDAP")

        if not all([self.host, self.database, self.username, self.password]):
            raise ConnectorException(
                "Teradata connection requires host, database, username, and password"
            )

        if not self.spark_session:
            raise ConnectorException("Spark session is required for Teradata connector")

    def connect(self) -> None:
        """Establish connection to Teradata."""
        try:
            self.logger.info(
                "Connecting to Teradata",
                host=self.host,
                database=self.database,
            )

            # Teradata uses JDBC with specific driver
            jdbc_url = (
                f"jdbc:teradata://{self.host}/"
                f"DATABASE={self.database},"
                f"LOGMECH={self.logmech}"
            )

            # Test connection
            test_df = (
                self.spark_session.read.format("jdbc")
                .option("url", jdbc_url)
                .option("dbtable", "(SELECT 1 AS test) AS t")
                .option("user", self.username)
                .option("password", self.password)
                .option("driver", "com.teradata.jdbc.TeraDriver")
                .load()
            )
            test_df.collect()

            self._is_connected = True
            self.logger.info("Successfully connected to Teradata")

        except Exception as e:
            raise ConnectionError(f"Failed to connect to Teradata: {str(e)}") from e

    def disconnect(self) -> None:
        """Close Teradata connection."""
        self._is_connected = False
        self.logger.info("Disconnected from Teradata")

    def _get_jdbc_url(self) -> str:
        """Get JDBC URL for Teradata."""
        return (
            f"jdbc:teradata://{self.host}/"
            f"DATABASE={self.database},"
            f"LOGMECH={self.logmech}"
        )

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
        Read data from Teradata.

        Args:
            query: SQL query (preferred method)
            table: Table name
            schema: Database name (defaults to configured database)
            filters: Pushdown filters
            columns: Columns to select
            limit: Maximum rows to return

        Returns:
            PySpark DataFrame
        """
        self._validate_connection()

        try:
            jdbc_url = self._get_jdbc_url()
            database = schema or self.database

            if query:
                self.logger.info("Executing SQL query on Teradata")
                df = (
                    self.spark_session.read.format("jdbc")
                    .option("url", jdbc_url)
                    .option("query", query)
                    .option("user", self.username)
                    .option("password", self.password)
                    .option("driver", "com.teradata.jdbc.TeraDriver")
                    .load()
                )
            elif table:
                full_table_name = f"{database}.{table}"
                self.logger.info("Reading table from Teradata", table=full_table_name)
                df = (
                    self.spark_session.read.format("jdbc")
                    .option("url", jdbc_url)
                    .option("dbtable", full_table_name)
                    .option("user", self.username)
                    .option("password", self.password)
                    .option("driver", "com.teradata.jdbc.TeraDriver")
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
                f"Failed to read data from Teradata: {str(e)}"
            ) from e

    def write_results(
        self,
        data: DataFrame,
        destination: str,
        mode: str = "overwrite",
        partition_by: Optional[List[str]] = None,
    ) -> None:
        """
        Write results to Teradata table.

        Args:
            data: DataFrame to write
            destination: Table name
            mode: Write mode
            partition_by: Not supported for Teradata
        """
        self._validate_connection()

        if partition_by:
            self.logger.warning("Partitioning not supported for Teradata writes")

        self.logger.info("Writing data to Teradata", destination=destination, mode=mode)

        try:
            jdbc_url = self._get_jdbc_url()

            data.write.format("jdbc").mode(mode).option("url", jdbc_url).option(
                "dbtable", destination
            ).option("user", self.username).option("password", self.password).option(
                "driver", "com.teradata.jdbc.TeraDriver"
            ).save()

            self.logger.info("Successfully wrote data to Teradata")

        except Exception as e:
            raise ConnectorException(
                f"Failed to write data to Teradata: {str(e)}"
            ) from e

    def get_schema(
        self,
        table: str,
        schema: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get schema for Teradata table.

        Args:
            table: Table name
            schema: Database name (defaults to configured database)

        Returns:
            Dictionary mapping column names to data types
        """
        self._validate_connection()

        database = schema or self.database
        full_table_name = f"{database}.{table}"

        try:
            jdbc_url = self._get_jdbc_url()
            df = (
                self.spark_session.read.format("jdbc")
                .option("url", jdbc_url)
                .option("dbtable", full_table_name)
                .option("user", self.username)
                .option("password", self.password)
                .option("driver", "com.teradata.jdbc.TeraDriver")
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
                f"Failed to get schema from Teradata: {str(e)}"
            ) from e

    def test_connection(self) -> bool:
        """
        Test Teradata connection.

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
                .option("driver", "com.teradata.jdbc.TeraDriver")
                .load()
            )
            test_df.collect()
            return True
        except Exception as e:
            self.logger.error("Teradata connection test failed", error=str(e))
            return False
