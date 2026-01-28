"""Multi-field validation rule executor."""

from typing import Any, Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count

from metadata.models import RuleCategory, ValidationRule
from rules.parser import parse_rule_expression
from utils.exceptions import RuleExecutionException
from utils.logger import get_logger


class MultiFieldValidator:
    """Validator for multi-field validation rules."""

    def __init__(self):
        """Initialize the validator."""
        self.logger = get_logger(self.__class__.__name__)

    def validate(
        self,
        dataframe: DataFrame,
        rule: ValidationRule,
        column_names: List[str],
        sample_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Execute multi-field validation rule.

        Args:
            dataframe: Input DataFrame
            rule: Validation rule
            column_names: List of columns involved in validation
            sample_size: Number of failed records to sample

        Returns:
            Dictionary with validation results
        """
        try:
            self.logger.info(
                "Executing multi-field validation",
                rule_id=str(rule.rule_id),
                columns=column_names,
            )

            # Parse rule expression with column mapping
            column_mapping = {col: col for col in column_names}
            rule_expression = parse_rule_expression(rule.rule_logic, column_mapping)

            # Apply validation - violations are where expression is False
            validation_result = ~rule_expression

            # Add validation column
            df_with_validation = dataframe.withColumn(
                "_validation_result", validation_result
            )

            # Count records
            total_count = dataframe.count()
            failed_count = df_with_validation.filter(col("_validation_result") == True).count()
            passed_count = total_count - failed_count

            # Calculate failure rate
            failure_rate = (failed_count / total_count * 100) if total_count > 0 else 0.0

            # Sample failed records
            sample_failed = []
            if failed_count > 0:
                failed_df = (
                    df_with_validation.filter(col("_validation_result") == True)
                    .select(*column_names)
                    .limit(sample_size)
                )
                sample_failed = [
                    {col: row[col] for col in column_names} for row in failed_df.collect()
                ]

            # Check threshold if specified
            threshold_passed = True
            if rule.threshold_value is not None:
                threshold_passed = failure_rate <= rule.threshold_value

            # Determine status
            status = "pass" if (failed_count == 0 and threshold_passed) else "fail"

            result = {
                "records_checked": total_count,
                "records_failed": failed_count,
                "records_passed": passed_count,
                "failure_rate": failure_rate,
                "sample_failed_records": sample_failed,
                "failure_details": {
                    "columns": column_names,
                    "rule_category": rule.rule_category.value,
                    "threshold_passed": threshold_passed,
                    "threshold_value": rule.threshold_value,
                },
                "status": status,
            }

            self.logger.info(
                "Multi-field validation completed",
                rule_id=str(rule.rule_id),
                records_checked=total_count,
                records_failed=failed_count,
                status=status,
            )

            return result

        except Exception as e:
            self.logger.exception(
                "Failed to execute multi-field validation",
                rule_id=str(rule.rule_id),
                error=str(e),
            )
            raise RuleExecutionException(
                f"Multi-field validation failed: {str(e)}"
            ) from e

    def validate_consistency(
        self,
        dataframe: DataFrame,
        column1: str,
        column2: str,
        relationship: str = "equals",
    ) -> Dict[str, Any]:
        """
        Validate consistency between two columns.

        Args:
            dataframe: Input DataFrame
            column1: First column name
            column2: Second column name
            relationship: Relationship type (equals, not_equals, greater_than, less_than)

        Returns:
            Validation results dictionary
        """
        from rules.functions import RuleFunctions

        if relationship == "equals":
            rule_expression = RuleFunctions.equals(col(column1), col(column2))
            rule_logic = f"equals(col('{column1}'), col('{column2}'))"
        elif relationship == "not_equals":
            rule_expression = RuleFunctions.not_equals(col(column1), col(column2))
            rule_logic = f"not_equals(col('{column1}'), col('{column2}'))"
        elif relationship == "greater_than":
            rule_expression = RuleFunctions.greater_than(col(column1), col(column2))
            rule_logic = f"greater_than(col('{column1}'), col('{column2}'))"
        elif relationship == "less_than":
            rule_expression = RuleFunctions.less_than(col(column1), col(column2))
            rule_logic = f"less_than(col('{column1}'), col('{column2}'))"
        else:
            raise RuleExecutionException(f"Unsupported relationship: {relationship}")

        temp_rule = ValidationRule(
            rule_name=f"Consistency Check - {relationship}",
            rule_type="multi_field",
            rule_category=RuleCategory.CONSISTENCY,
            severity_level="medium",
            rule_logic=rule_logic,
            created_by="system",
        )

        return self.validate(dataframe, temp_rule, [column1, column2])

    def validate_business_logic(
        self,
        dataframe: DataFrame,
        rule_logic: str,
        column_names: List[str],
    ) -> Dict[str, Any]:
        """
        Validate custom business logic across multiple fields.

        Args:
            dataframe: Input DataFrame
            rule_logic: Custom rule expression
            column_names: Columns involved in validation

        Returns:
            Validation results dictionary
        """
        temp_rule = ValidationRule(
            rule_name="Business Logic Check",
            rule_type="multi_field",
            rule_category=RuleCategory.CUSTOM,
            severity_level="high",
            rule_logic=rule_logic,
            created_by="system",
        )

        return self.validate(dataframe, temp_rule, column_names)
