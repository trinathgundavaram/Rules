"""Aurora PostgreSQL connector implementation."""

from typing import Any, Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql import SparkSession

from connectors.base import BaseConnector
from utils.exceptions import ConnectionError, ConnectorException
from utils.logger import get_logger


class AuroraPostgreSQLConnector(BaseConnector):
    """Connector for Aurora PostgreSQL data sources."""

    def __init__(
        self,
        connection_config: Dict[str, Any],
        spark_session: Optional[SparkSession] = None,
    ):
        """
        Initialize Aurora PostgreSQL connector.

        Args:
            connection_config: Must contain 'host', 'database', 'username',
                              'password', 'port', and optionally 'schema'
            spark_session: Spark session (required)
        """
        super().__init__(connection_config, spark_session)
        self.host = connection_config.get("host")
        self.port = connection_config.get("port", 5432)
        self.database = connection_config.get("database")
        self.username = connection_config.get("username")
        self.password = connection_config.get("password")
        self.schema = connection_config.get("schema", "public")
        self.sslmode = connection_config.get("sslmode", "require")

        if not all([self.host, self.database, self.username, self.password]):
            raise ConnectorException(
                "Aurora PostgreSQL connection requires host, database, username, and password"
            )

        if not self.spark_session:
            raise ConnectorException(
                "Spark session is required for Aurora PostgreSQL connector"
            )

    def connect(self) -> None:
        """Establish connection to Aurora PostgreSQL."""
        try:
            self.logger.info(
                "Connecting to Aurora PostgreSQL",
                host=self.host,
                database=self.database,
            )

            # PostgreSQL JDBC URL
            jdbc_url = (
                f"jdbc:postgresql://{self.host}:{self.port}/{self.database}"
                f"?sslmode={self.sslmode}"
            )

            # Test connection
            test_df = (
                self.spark_session.read.format("jdbc")
                .option("url", jdbc_url)
                .option("dbtable", "(SELECT 1 AS test) AS t")
                .option("user", self.username)
                .option("password", self.password)
                .option("driver", "org.postgresql.Driver")
                .load()
            )
            test_df.collect()

            self._is_connected = True
            self.logger.info("Successfully connected to Aurora PostgreSQL")

        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Aurora PostgreSQL: {str(e)}"
            ) from e

    def disconnect(self) -> None:
        """Close Aurora PostgreSQL connection."""
        self._is_connected = False
        self.logger.info("Disconnected from Aurora PostgreSQL")

    def _get_jdbc_url(self) -> str:
        """Get JDBC URL for Aurora PostgreSQL."""
        return (
            f"jdbc:postgresql://{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.sslmode}"
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
        Read data from Aurora PostgreSQL.

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
                self.logger.info("Executing SQL query on Aurora PostgreSQL")
                df = (
                    self.spark_session.read.format("jdbc")
                    .option("url", jdbc_url)
                    .option("query", query)
                    .option("user", self.username)
                    .option("password", self.password)
                    .option("driver", "org.postgresql.Driver")
                    .load()
                )
            elif table:
                full_table_name = f"{schema_name}.{table}"
                self.logger.info(
                    "Reading table from Aurora PostgreSQL", table=full_table_name
                )
                df = (
                    self.spark_session.read.format("jdbc")
                    .option("url", jdbc_url)
                    .option("dbtable", full_table_name)
                    .option("user", self.username)
                    .option("password", self.password)
                    .option("driver", "org.postgresql.Driver")
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
                f"Failed to read data from Aurora PostgreSQL: {str(e)}"
            ) from e

    def write_results(
        self,
        data: DataFrame,
        destination: str,
        mode: str = "overwrite",
        partition_by: Optional[List[str]] = None,
    ) -> None:
        """
        Write results to Aurora PostgreSQL table.

        Args:
            data: DataFrame to write
            destination: Table name (can include schema.table)
            mode: Write mode
            partition_by: Not supported for PostgreSQL
        """
        self._validate_connection()

        if partition_by:
            self.logger.warning("Partitioning not supported for PostgreSQL writes")

        self.logger.info(
            "Writing data to Aurora PostgreSQL", destination=destination, mode=mode
        )

        try:
            jdbc_url = self._get_jdbc_url()

            data.write.format("jdbc").mode(mode).option("url", jdbc_url).option(
                "dbtable", destination
            ).option("user", self.username).option("password", self.password).option(
                "driver", "org.postgresql.Driver"
            ).save()

            self.logger.info("Successfully wrote data to Aurora PostgreSQL")

        except Exception as e:
            raise ConnectorException(
                f"Failed to write data to Aurora PostgreSQL: {str(e)}"
            ) from e

    def get_schema(
        self,
        table: str,
        schema: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get schema for Aurora PostgreSQL table.

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
                .option("driver", "org.postgresql.Driver")
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
                f"Failed to get schema from Aurora PostgreSQL: {str(e)}"
            ) from e

    def test_connection(self) -> bool:
        """
        Test Aurora PostgreSQL connection.

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
                .option("driver", "org.postgresql.Driver")
                .load()
            )
            test_df.collect()
            return True
        except Exception as e:
            self.logger.error(
                "Aurora PostgreSQL connection test failed", error=str(e)
            )
            return False
