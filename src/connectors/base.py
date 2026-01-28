"""Base connector interface for data source abstraction."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql import SparkSession

from src.utils.exceptions import ConnectorException
from src.utils.logger import get_logger


class BaseConnector(ABC):
    """Abstract base class for all data connectors."""

    def __init__(
        self,
        connection_config: Dict[str, Any],
        spark_session: Optional[SparkSession] = None,
    ):
        """
        Initialize the connector.

        Args:
            connection_config: Connection configuration dictionary
            spark_session: Optional Spark session (for PySpark connectors)
        """
        self.connection_config = connection_config
        self.spark_session = spark_session
        self.logger = get_logger(self.__class__.__name__)
        self._connection = None
        self._is_connected = False

    @abstractmethod
    def connect(self) -> None:
        """
        Establish connection to the data source.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the data source."""
        pass

    @abstractmethod
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
        Read data from the source.

        Args:
            query: SQL query string (optional)
            table: Table name (optional, used with schema)
            schema: Schema/database name (optional)
            filters: Dictionary of column filters (optional)
            columns: List of columns to select (optional)
            limit: Maximum number of rows to return (optional)

        Returns:
            PySpark DataFrame

        Raises:
            ConnectorException: If read operation fails
        """
        pass

    @abstractmethod
    def write_results(
        self,
        data: DataFrame,
        destination: str,
        mode: str = "overwrite",
        partition_by: Optional[List[str]] = None,
    ) -> None:
        """
        Write validation results to destination.

        Args:
            data: DataFrame to write
            destination: Destination path/table
            mode: Write mode (overwrite, append, error, ignore)
            partition_by: List of columns to partition by (optional)

        Raises:
            ConnectorException: If write operation fails
        """
        pass

    @abstractmethod
    def get_schema(
        self,
        table: str,
        schema: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get schema information for a table.

        Args:
            table: Table name
            schema: Schema/database name (optional)

        Returns:
            Dictionary mapping column names to data types

        Raises:
            ConnectorException: If schema retrieval fails
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the connection to the data source.

        Returns:
            True if connection is successful, False otherwise
        """
        pass

    def is_connected(self) -> bool:
        """
        Check if connector is currently connected.

        Returns:
            True if connected, False otherwise
        """
        return self._is_connected

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def _validate_connection(self) -> None:
        """
        Validate that connection is established.

        Raises:
            ConnectionError: If not connected
        """
        if not self._is_connected:
            raise ConnectorException("Not connected to data source. Call connect() first.")

    def _apply_filters(
        self, df: DataFrame, filters: Optional[Dict[str, Any]]
    ) -> DataFrame:
        """
        Apply filters to DataFrame.

        Args:
            df: Input DataFrame
            filters: Dictionary of column filters

        Returns:
            Filtered DataFrame
        """
        if not filters:
            return df

        from pyspark.sql.functions import col

        for column, value in filters.items():
            if isinstance(value, list):
                df = df.filter(col(column).isin(value))
            elif isinstance(value, dict):
                # Support range queries: {"gte": 10, "lte": 20}
                if "gte" in value:
                    df = df.filter(col(column) >= value["gte"])
                if "lte" in value:
                    df = df.filter(col(column) <= value["lte"])
                if "gt" in value:
                    df = df.filter(col(column) > value["gt"])
                if "lt" in value:
                    df = df.filter(col(column) < value["lt"])
            else:
                df = df.filter(col(column) == value)

        return df

    def _select_columns(self, df: DataFrame, columns: Optional[List[str]]) -> DataFrame:
        """
        Select specific columns from DataFrame.

        Args:
            df: Input DataFrame
            columns: List of column names to select

        Returns:
            DataFrame with selected columns
        """
        if not columns:
            return df

        from pyspark.sql.functions import col

        return df.select([col(c) for c in columns])
