"""Rule expression parser for SQL/Python-style expressions."""

import ast
import re
from typing import Any, Dict, List, Optional

from pyspark.sql import Column
from pyspark.sql.functions import col

from rules.functions import FUNCTION_REGISTRY, RuleFunctions
from utils.exceptions import RuleParseException
from utils.logger import get_logger


class RuleParser:
    """Parser for rule expressions into PySpark column expressions."""

    def __init__(self):
        """Initialize the parser."""
        self.logger = get_logger(self.__class__.__name__)

    def parse(
        self,
        expression: str,
        column_mapping: Optional[Dict[str, str]] = None,
    ) -> Column:
        """
        Parse a rule expression into a PySpark column expression.

        Supports:
        - Column references: col('column_name') or column_name
        - Built-in functions: is_null(col('email')), regex_match(col('phone'), pattern)
        - SQL-style WHERE clauses: col('age') > 18 AND col('status') = 'active'
        - Python lambda expressions: lambda x: x.age > 18

        Args:
            expression: Rule expression string
            column_mapping: Optional mapping of column aliases to actual names

        Returns:
            PySpark Column expression

        Raises:
            RuleParseException: If parsing fails
        """
        try:
            expression = expression.strip()

            # Handle SQL WHERE clause style
            if self._is_sql_style(expression):
                return self._parse_sql_style(expression, column_mapping)

            # Handle Python lambda
            if expression.startswith("lambda"):
                return self._parse_lambda(expression, column_mapping)

            # Handle function call style
            if "(" in expression and ")" in expression:
                return self._parse_function_call(expression, column_mapping)

            # Handle simple column reference
            return self._parse_column_reference(expression, column_mapping)

        except Exception as e:
            raise RuleParseException(
                f"Failed to parse rule expression: {expression}. Error: {str(e)}"
            ) from e

    def _is_sql_style(self, expression: str) -> bool:
        """
        Check if expression is SQL WHERE clause style.

        Args:
            expression: Expression string

        Returns:
            True if SQL style
        """
        sql_keywords = ["AND", "OR", "NOT", "IN", "LIKE", "BETWEEN"]
        return any(keyword in expression.upper() for keyword in sql_keywords)

    def _parse_sql_style(
        self, expression: str, column_mapping: Optional[Dict[str, str]] = None
    ) -> Column:
        """
        Parse SQL WHERE clause style expression.

        Args:
            expression: SQL-style expression
            column_mapping: Optional column mapping

        Returns:
            PySpark Column expression
        """
        # Replace common SQL operators with Python equivalents
        expression = expression.replace(" AND ", " & ").replace(" and ", " & ")
        expression = expression.replace(" OR ", " | ").replace(" or ", " | ")
        expression = expression.replace(" NOT ", " ~").replace(" not ", " ~")
        expression = expression.replace(" = ", " == ").replace("=", "==")

        # Handle column references
        expression = self._replace_column_references(expression, column_mapping)

        # Handle function calls
        expression = self._replace_function_calls(expression)

        # Evaluate as Python expression
        try:
            # Create safe evaluation context
            safe_dict = {
                "col": col,
                "__builtins__": {},
            }
            # Add function registry
            safe_dict.update(FUNCTION_REGISTRY)

            return eval(expression, safe_dict)
        except Exception as e:
            raise RuleParseException(f"Failed to evaluate SQL expression: {str(e)}") from e

    def _parse_lambda(
        self, expression: str, column_mapping: Optional[Dict[str, str]] = None
    ) -> Column:
        """
        Parse Python lambda expression.

        Args:
            expression: Lambda expression
            column_mapping: Optional column mapping

        Returns:
            PySpark Column expression
        """
        # Parse lambda AST
        try:
            tree = ast.parse(expression, mode="eval")
            if isinstance(tree.body, ast.Lambda):
                # Convert lambda to column expression
                # This is a simplified version - full implementation would traverse AST
                raise RuleParseException(
                    "Full lambda parsing not yet implemented. Use function call or SQL style."
                )
            else:
                raise RuleParseException("Invalid lambda expression")
        except SyntaxError as e:
            raise RuleParseException(f"Invalid lambda syntax: {str(e)}") from e

    def _parse_function_call(
        self, expression: str, column_mapping: Optional[Dict[str, str]] = None
    ) -> Column:
        """
        Parse function call style expression.

        Args:
            expression: Function call expression
            column_mapping: Optional column mapping

        Returns:
            PySpark Column expression
        """
        # Replace column references
        expression = self._replace_column_references(expression, column_mapping)

        # Create safe evaluation context
        safe_dict = {
            "col": col,
            "__builtins__": {},
        }
        safe_dict.update(FUNCTION_REGISTRY)

        try:
            return eval(expression, safe_dict)
        except Exception as e:
            raise RuleParseException(f"Failed to evaluate function call: {str(e)}") from e

    def _parse_column_reference(
        self, expression: str, column_mapping: Optional[Dict[str, str]] = None
    ) -> Column:
        """
        Parse simple column reference.

        Args:
            expression: Column name
            column_mapping: Optional column mapping

        Returns:
            PySpark Column expression
        """
        column_name = expression.strip()
        if column_mapping and column_name in column_mapping:
            column_name = column_mapping[column_name]

        return col(column_name)

    def _replace_column_references(
        self, expression: str, column_mapping: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Replace column references in expression with col() calls.

        Args:
            expression: Expression string
            column_mapping: Optional column mapping

        Returns:
            Expression with column references replaced
        """
        # Pattern to match column references (not already in col())
        # Matches: column_name, 'column_name', "column_name"
        pattern = r"(?<!col\(['\"])(\b\w+\b|['\"][\w_]+['\"])(?!['\"]\))"

        def replace_match(match):
            col_ref = match.group(1).strip("'\"")
            if column_mapping and col_ref in column_mapping:
                col_ref = column_mapping[col_ref]
            return f"col('{col_ref}')"

        # Only replace if not already a function call or number
        result = re.sub(pattern, replace_match, expression)
        return result

    def _replace_function_calls(self, expression: str) -> str:
        """
        Replace function calls with PySpark equivalents.

        Args:
            expression: Expression string

        Returns:
            Expression with function calls replaced
        """
        # This is a simplified version - full implementation would handle
        # more complex function call patterns
        return expression


def parse_rule_expression(
    expression: str,
    column_mapping: Optional[Dict[str, str]] = None,
) -> Column:
    """
    Convenience function to parse a rule expression.

    Args:
        expression: Rule expression string
        column_mapping: Optional column mapping

    Returns:
        PySpark Column expression
    """
    parser = RuleParser()
    return parser.parse(expression, column_mapping)
