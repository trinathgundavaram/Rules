"""SQL Server connector implementation."""

from typing import Any, Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql import SparkSession

from connectors.base import BaseConnector
from utils.exceptions import ConnectionError, ConnectorException
from utils.logger import get_logger


class SQLServerConnector(BaseConnector):
    """Connector for SQL Server data sources."""

    def __init__(
        self,
        connection_config: Dict[str, Any],
        spark_session: Optional[SparkSession] = None,
    ):
        """
        Initialize SQL Server connector.

        Args:
            connection_config: Must contain 'server', 'database', 'username',
                              'password', and optionally 'port', 'schema'
            spark_session: Spark session (required)
        """
        super().__init__(connection_config, spark_session)
        self.server = connection_config.get("server")
        self.port = connection_config.get("port", 1433)
        self.database = connection_config.get("database")
        self.username = connection_config.get("username")
        self.password = connection_config.get("password")
        self.schema = connection_config.get("schema", "dbo")
        self.encrypt = connection_config.get("encrypt", True)
        self.trust_server_certificate = connection_config.get(
            "trust_server_certificate", False
        )

        if not all([self.server, self.database, self.username, self.password]):
            raise ConnectorException(
                "SQL Server connection requires server, database, username, and password"
            )

        if not self.spark_session:
            raise ConnectorException("Spark session is required for SQL Server connector")

    def connect(self) -> None:
        """Establish connection to SQL Server."""
        try:
            self.logger.info(
                "Connecting to SQL Server",
                server=self.server,
                database=self.database,
            )

            # Configure Spark JDBC connection
            jdbc_url = (
                f"jdbc:sqlserver://{self.server}:{self.port};"
                f"database={self.database};"
                f"encrypt={str(self.encrypt).lower()};"
                f"trustServerCertificate={str(self.trust_server_certificate).lower()}"
            )

            # Test connection with a simple query
            test_df = (
                self.spark_session.read.format("jdbc")
                .option("url", jdbc_url)
                .option("dbtable", "(SELECT 1 AS test) AS t")
                .option("user", self.username)
                .option("password", self.password)
                .load()
            )
            test_df.collect()

            self._is_connected = True
            self.logger.info("Successfully connected to SQL Server")

        except Exception as e:
            raise ConnectionError(f"Failed to connect to SQL Server: {str(e)}") from e

    def disconnect(self) -> None:
        """Close SQL Server connection."""
        self._is_connected = False
        self.logger.info("Disconnected from SQL Server")

    def _get_jdbc_url(self) -> str:
        """Get JDBC URL for SQL Server."""
        return (
            f"jdbc:sqlserver://{self.server}:{self.port};"
            f"database={self.database};"
            f"encrypt={str(self.encrypt).lower()};"
            f"trustServerCertificate={str(self.trust_server_certificate).lower()}"
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
        Read data from SQL Server.

        Args:
            query: SQL query (preferred method)
            table: Table name (used with schema)
            schema: Schema name (defaults to configured schema)
            filters: Pushdown filters (limited support)
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
                self.logger.info("Executing SQL query on SQL Server")
                # Use query parameter for custom SQL
                df = (
                    self.spark_session.read.format("jdbc")
                    .option("url", jdbc_url)
                    .option("query", query)
                    .option("user", self.username)
                    .option("password", self.password)
                    .load()
                )
            elif table:
                full_table_name = f"{schema_name}.{table}"
                self.logger.info("Reading table from SQL Server", table=full_table_name)
                df = (
                    self.spark_session.read.format("jdbc")
                    .option("url", jdbc_url)
                    .option("dbtable", full_table_name)
                    .option("user", self.username)
                    .option("password", self.password)
                    .load()
                )
            else:
                raise ConnectorException("Either query or table must be provided")

            # Apply filters (pushdown may be limited)
            df = self._apply_filters(df, filters)

            # Select columns
            df = self._select_columns(df, columns)

            # Apply limit
            if limit:
                df = df.limit(limit)

            return df

        except Exception as e:
            raise ConnectorException(
                f"Failed to read data from SQL Server: {str(e)}"
            ) from e

    def write_results(
        self,
        data: DataFrame,
        destination: str,
        mode: str = "overwrite",
        partition_by: Optional[List[str]] = None,
    ) -> None:
        """
        Write results to SQL Server table.

        Args:
            data: DataFrame to write
            destination: Table name (can include schema.table)
            mode: Write mode (overwrite, append)
            partition_by: Not supported for SQL Server
        """
        self._validate_connection()

        if partition_by:
            self.logger.warning("Partitioning not supported for SQL Server writes")

        self.logger.info("Writing data to SQL Server", destination=destination, mode=mode)

        try:
            jdbc_url = self._get_jdbc_url()

            data.write.format("jdbc").mode(mode).option("url", jdbc_url).option(
                "dbtable", destination
            ).option("user", self.username).option("password", self.password).save()

            self.logger.info("Successfully wrote data to SQL Server")

        except Exception as e:
            raise ConnectorException(
                f"Failed to write data to SQL Server: {str(e)}"
            ) from e

    def get_schema(
        self,
        table: str,
        schema: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get schema for SQL Server table.

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
                f"Failed to get schema from SQL Server: {str(e)}"
            ) from e

    def test_connection(self) -> bool:
        """
        Test SQL Server connection.

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
                .load()
            )
            test_df.collect()
            return True
        except Exception as e:
            self.logger.error("SQL Server connection test failed", error=str(e))
            return False
