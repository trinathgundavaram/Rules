"""Built-in functions library for rule expressions."""

import re
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from pyspark.sql import Column
from pyspark.sql.functions import (
    col,
    current_timestamp,
    datediff,
    isnan,
    isnull,
    length,
    lower,
    regexp_extract,
    trim,
    upper,
    when,
)


class RuleFunctions:
    """Library of built-in functions for rule expressions."""

    @staticmethod
    def is_null(column: Column) -> Column:
        """
        Check if column value is null.

        Args:
            column: PySpark column

        Returns:
            Boolean column
        """
        return isnull(column)

    @staticmethod
    def is_not_null(column: Column) -> Column:
        """
        Check if column value is not null.

        Args:
            column: PySpark column

        Returns:
            Boolean column
        """
        return ~isnull(column)

    @staticmethod
    def is_empty(column: Column) -> Column:
        """
        Check if column value is empty string or null.

        Args:
            column: PySpark column

        Returns:
            Boolean column
        """
        return (isnull(column)) | (trim(column) == "")

    @staticmethod
    def is_not_empty(column: Column) -> Column:
        """
        Check if column value is not empty.

        Args:
            column: PySpark column

        Returns:
            Boolean column
        """
        return ~RuleFunctions.is_empty(column)

    @staticmethod
    def length_check(column: Column, min_length: Optional[int] = None, max_length: Optional[int] = None) -> Column:
        """
        Check if column value length is within range.

        Args:
            column: PySpark column
            min_length: Minimum length (optional)
            max_length: Maximum length (optional)

        Returns:
            Boolean column
        """
        col_length = length(trim(column))
        result = when(isnull(column), False)
        
        if min_length is not None and max_length is not None:
            result = result.when((col_length >= min_length) & (col_length <= max_length), True)
        elif min_length is not None:
            result = result.when(col_length >= min_length, True)
        elif max_length is not None:
            result = result.when(col_length <= max_length, True)
        else:
            result = result.otherwise(True)
            
        return result.otherwise(False)

    @staticmethod
    def regex_match(column: Column, pattern: str) -> Column:
        """
        Check if column value matches regex pattern.

        Args:
            column: PySpark column
            pattern: Regex pattern string

        Returns:
            Boolean column
        """
        return regexp_extract(column, pattern, 0) != ""

    @staticmethod
    def is_email(column: Column) -> Column:
        """
        Check if column value is a valid email address.

        Args:
            column: PySpark column

        Returns:
            Boolean column
        """
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return RuleFunctions.regex_match(column, email_pattern)

    @staticmethod
    def is_phone(column: Column) -> Column:
        """
        Check if column value is a valid phone number.

        Args:
            column: PySpark column

        Returns:
            Boolean column
        """
        # Supports formats: (123) 456-7890, 123-456-7890, 123.456.7890, 1234567890
        phone_pattern = r"^[\d\s\-\(\)\.]+$"
        cleaned = regexp_extract(column, r"\d", 0)
        return (RuleFunctions.regex_match(column, phone_pattern)) & (length(cleaned) >= 10)

    @staticmethod
    def is_numeric(column: Column) -> Column:
        """
        Check if column value is numeric.

        Args:
            column: PySpark column

        Returns:
            Boolean column
        """
        return ~isnan(column) & ~isnull(column)

    @staticmethod
    def range_check(
        column: Column,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        inclusive: bool = True,
    ) -> Column:
        """
        Check if column value is within numeric range.

        Args:
            column: PySpark column
            min_value: Minimum value (optional)
            max_value: Maximum value (optional)
            inclusive: Whether range is inclusive (default True)

        Returns:
            Boolean column
        """
        result = when(isnull(column), False)
        
        if min_value is not None and max_value is not None:
            if inclusive:
                result = result.when((column >= min_value) & (column <= max_value), True)
            else:
                result = result.when((column > min_value) & (column < max_value), True)
        elif min_value is not None:
            if inclusive:
                result = result.when(column >= min_value, True)
            else:
                result = result.when(column > min_value, True)
        elif max_value is not None:
            if inclusive:
                result = result.when(column <= max_value, True)
            else:
                result = result.when(column < max_value, True)
        else:
            result = result.otherwise(True)
            
        return result.otherwise(False)

    @staticmethod
    def date_diff(column1: Column, column2: Column, unit: str = "days") -> Column:
        """
        Calculate difference between two date columns.

        Args:
            column1: First date column
            column2: Second date column
            unit: Unit of difference (days, hours, minutes)

        Returns:
            Numeric column with difference
        """
        diff_seconds = datediff(column1, column2)
        
        if unit == "days":
            return diff_seconds
        elif unit == "hours":
            return diff_seconds * 24
        elif unit == "minutes":
            return diff_seconds * 24 * 60
        else:
            return diff_seconds

    @staticmethod
    def is_fresh(column: Column, max_age_days: int, reference_date: Optional[Column] = None) -> Column:
        """
        Check if date column is fresh (within max_age_days).

        Args:
            column: Date column
            max_age_days: Maximum age in days
            reference_date: Reference date column (defaults to current timestamp)

        Returns:
            Boolean column
        """
        ref_date = reference_date or current_timestamp()
        age_days = RuleFunctions.date_diff(ref_date, column, "days")
        return age_days <= max_age_days

    @staticmethod
    def is_in_list(column: Column, value_list: list) -> Column:
        """
        Check if column value is in a list of values.

        Args:
            column: PySpark column
            value_list: List of allowed values

        Returns:
            Boolean column
        """
        return column.isin(value_list)

    @staticmethod
    def is_not_in_list(column: Column, value_list: list) -> Column:
        """
        Check if column value is not in a list of values.

        Args:
            column: PySpark column
            value_list: List of disallowed values

        Returns:
            Boolean column
        """
        return ~column.isin(value_list)

    @staticmethod
    def equals(column1: Column, column2: Column) -> Column:
        """
        Check if two columns are equal.

        Args:
            column1: First column
            column2: Second column

        Returns:
            Boolean column
        """
        return column1 == column2

    @staticmethod
    def not_equals(column1: Column, column2: Column) -> Column:
        """
        Check if two columns are not equal.

        Args:
            column1: First column
            column2: Second column

        Returns:
            Boolean column
        """
        return column1 != column2

    @staticmethod
    def greater_than(column1: Column, column2: Column) -> Column:
        """
        Check if column1 > column2.

        Args:
            column1: First column
            column2: Second column

        Returns:
            Boolean column
        """
        return column1 > column2

    @staticmethod
    def less_than(column1: Column, column2: Column) -> Column:
        """
        Check if column1 < column2.

        Args:
            column1: First column
            column2: Second column

        Returns:
            Boolean column
        """
        return column1 < column2


# Registry of available functions
FUNCTION_REGISTRY: Dict[str, Callable] = {
    "is_null": RuleFunctions.is_null,
    "is_not_null": RuleFunctions.is_not_null,
    "is_empty": RuleFunctions.is_empty,
    "is_not_empty": RuleFunctions.is_not_empty,
    "length_check": RuleFunctions.length_check,
    "regex_match": RuleFunctions.regex_match,
    "is_email": RuleFunctions.is_email,
    "is_phone": RuleFunctions.is_phone,
    "is_numeric": RuleFunctions.is_numeric,
    "range_check": RuleFunctions.range_check,
    "date_diff": RuleFunctions.date_diff,
    "is_fresh": RuleFunctions.is_fresh,
    "is_in_list": RuleFunctions.is_in_list,
    "is_not_in_list": RuleFunctions.is_not_in_list,
    "equals": RuleFunctions.equals,
    "not_equals": RuleFunctions.not_equals,
    "greater_than": RuleFunctions.greater_than,
    "less_than": RuleFunctions.less_than,
}
