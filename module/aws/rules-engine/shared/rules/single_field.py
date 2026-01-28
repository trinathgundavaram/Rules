"""Single-field validation rule executor."""

from typing import Any, Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count, sum as spark_sum, when

from metadata.models import RuleCategory, ValidationRule
from rules.parser import parse_rule_expression
from utils.exceptions import RuleExecutionException
from utils.logger import get_logger


class SingleFieldValidator:
    """Validator for single-field validation rules."""

    def __init__(self):
        """Initialize the validator."""
        self.logger = get_logger(self.__class__.__name__)

    def validate(
        self,
        dataframe: DataFrame,
        rule: ValidationRule,
        column_name: str,
        sample_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Execute single-field validation rule.

        Args:
            dataframe: Input DataFrame
            rule: Validation rule
            column_name: Column to validate
            sample_size: Number of failed records to sample

        Returns:
            Dictionary with validation results:
            - records_checked: Total records checked
            - records_failed: Number of failed records
            - records_passed: Number of passed records
            - failure_rate: Percentage of failures
            - sample_failed_records: Sample of failed records
            - failure_details: Additional failure information
        """
        try:
            self.logger.info(
                "Executing single-field validation",
                rule_id=str(rule.rule_id),
                column=column_name,
            )

            # Parse rule expression
            rule_expression = parse_rule_expression(
                rule.rule_logic,
                column_mapping={column_name: column_name},
            )

            # Apply validation - create a boolean column indicating pass/fail
            # For validation rules, we typically check if the condition is FALSE (i.e., violation)
            # So if rule says "is_not_null", we check for violations where is_null is True
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
                    .select(column_name)
                    .limit(sample_size)
                )
                sample_failed = [
                    {column_name: row[column_name]} for row in failed_df.collect()
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
                    "column": column_name,
                    "rule_category": rule.rule_category.value,
                    "threshold_passed": threshold_passed,
                    "threshold_value": rule.threshold_value,
                },
                "status": status,
            }

            self.logger.info(
                "Single-field validation completed",
                rule_id=str(rule.rule_id),
                records_checked=total_count,
                records_failed=failed_count,
                status=status,
            )

            return result

        except Exception as e:
            self.logger.exception(
                "Failed to execute single-field validation",
                rule_id=str(rule.rule_id),
                error=str(e),
            )
            raise RuleExecutionException(
                f"Single-field validation failed: {str(e)}"
            ) from e

    def validate_completeness(
        self,
        dataframe: DataFrame,
        column_name: str,
        allow_empty_strings: bool = False,
    ) -> Dict[str, Any]:
        """
        Validate completeness (null/empty checks).

        Args:
            dataframe: Input DataFrame
            column_name: Column to validate
            allow_empty_strings: Whether empty strings are considered valid

        Returns:
            Validation results dictionary
        """
        from rules.functions import RuleFunctions

        if allow_empty_strings:
            rule_expression = RuleFunctions.is_not_null(col(column_name))
        else:
            rule_expression = RuleFunctions.is_not_empty(col(column_name))

        # Create temporary rule for execution
        temp_rule = ValidationRule(
            rule_name="Completeness Check",
            rule_type="single_field",
            rule_category=RuleCategory.COMPLETENESS,
            severity_level="high",
            rule_logic=f"is_not_empty(col('{column_name}'))" if not allow_empty_strings else f"is_not_null(col('{column_name}'))",
            created_by="system",
        )

        return self.validate(dataframe, temp_rule, column_name)

    def validate_accuracy(
        self,
        dataframe: DataFrame,
        column_name: str,
        validation_type: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Validate accuracy (range, regex, format checks).

        Args:
            dataframe: Input DataFrame
            column_name: Column to validate
            validation_type: Type of validation (range, regex, email, phone, etc.)
            **kwargs: Additional validation parameters

        Returns:
            Validation results dictionary
        """
        from rules.functions import RuleFunctions

        if validation_type == "range":
            min_val = kwargs.get("min_value")
            max_val = kwargs.get("max_value")
            rule_expression = RuleFunctions.range_check(
                col(column_name), min_val, max_val
            )
            rule_logic = f"range_check(col('{column_name}'), {min_val}, {max_val})"
        elif validation_type == "regex":
            pattern = kwargs.get("pattern")
            rule_expression = RuleFunctions.regex_match(col(column_name), pattern)
            rule_logic = f"regex_match(col('{column_name}'), '{pattern}')"
        elif validation_type == "email":
            rule_expression = RuleFunctions.is_email(col(column_name))
            rule_logic = f"is_email(col('{column_name}'))"
        elif validation_type == "phone":
            rule_expression = RuleFunctions.is_phone(col(column_name))
            rule_logic = f"is_phone(col('{column_name}'))"
        else:
            raise RuleExecutionException(f"Unsupported validation type: {validation_type}")

        temp_rule = ValidationRule(
            rule_name=f"Accuracy Check - {validation_type}",
            rule_type="single_field",
            rule_category=RuleCategory.ACCURACY,
            severity_level="high",
            rule_logic=rule_logic,
            created_by="system",
        )

        return self.validate(dataframe, temp_rule, column_name)
