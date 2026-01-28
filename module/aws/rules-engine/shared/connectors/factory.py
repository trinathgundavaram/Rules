"""Factory for creating connector instances."""

from typing import Any, Dict, Optional

from pyspark.sql import SparkSession

from connectors.base import BaseConnector
from connectors.aurora_postgresql import AuroraPostgreSQLConnector
from connectors.databricks import DatabricksConnector
from connectors.redshift import RedshiftConnector
from connectors.s3 import S3Connector
from connectors.sqlserver import SQLServerConnector
from connectors.teradata import TeradataConnector
from metadata.models import SourceType
from utils.exceptions import ConfigurationException
from utils.logger import get_logger


class ConnectorFactory:
    """Factory for creating data connector instances."""

    _connector_classes: Dict[str, type[BaseConnector]] = {
        SourceType.DATABRICKS: DatabricksConnector,
        SourceType.SQL_SERVER: SQLServerConnector,
        SourceType.TERADATA: TeradataConnector,
        SourceType.S3: S3Connector,
        SourceType.REDSHIFT: RedshiftConnector,
        SourceType.AURORA_POSTGRESQL: AuroraPostgreSQLConnector,
    }

    @classmethod
    def create_connector(
        cls,
        source_type: str,
        connection_config: Dict[str, Any],
        spark_session: Optional[SparkSession] = None,
    ) -> BaseConnector:
        """
        Create a connector instance based on source type.

        Args:
            source_type: Type of data source
            connection_config: Connection configuration
            spark_session: Optional Spark session

        Returns:
            Connector instance

        Raises:
            ConfigurationException: If source type is not supported
        """
        logger = get_logger(cls.__name__)

        # Normalize source type
        source_type = source_type.lower()

        if source_type not in cls._connector_classes:
            supported_types = ", ".join(cls._connector_classes.keys())
            raise ConfigurationException(
                f"Unsupported source type: {source_type}. "
                f"Supported types: {supported_types}"
            )

        connector_class = cls._connector_classes[source_type]
        logger.info(
            f"Creating {source_type} connector",
            source_type=source_type,
        )

        return connector_class(connection_config, spark_session)

    @classmethod
    def register_connector(
        cls,
        source_type: str,
        connector_class: type[BaseConnector],
    ) -> None:
        """
        Register a custom connector class.

        Args:
            source_type: Source type identifier
            connector_class: Connector class to register
        """
        cls._connector_classes[source_type.lower()] = connector_class
