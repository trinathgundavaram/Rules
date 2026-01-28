"""Custom exceptions for the Rules Engine Framework."""

from typing import Optional


class RulesEngineException(Exception):
    """Base exception for all Rules Engine errors."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        """
        Initialize the exception.

        Args:
            message: Error message
            error_code: Optional error code for programmatic handling
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class ConnectorException(RulesEngineException):
    """Exception raised for connector-related errors."""

    pass


class ConnectionError(ConnectorException):
    """Exception raised when connection to data source fails."""

    pass


class AuthenticationError(ConnectorException):
    """Exception raised when authentication fails."""

    pass


class RuleExecutionException(RulesEngineException):
    """Exception raised during rule execution."""

    pass


class RuleParseException(RuleExecutionException):
    """Exception raised when parsing rule logic fails."""

    pass


class MetadataException(RulesEngineException):
    """Exception raised for metadata repository errors."""

    pass


class ValidationException(RulesEngineException):
    """Exception raised during data validation."""

    pass


class ConfigurationException(RulesEngineException):
    """Exception raised for configuration errors."""

    pass
