"""Main rule executor for orchestrating validation."""

import time
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pyspark.sql import DataFrame
from pyspark.sql import SparkSession

from src.connectors.base import BaseConnector
from src.connectors.factory import ConnectorFactory
from src.metadata.models import (
    ExecutionLog,
    ExecutionStatus,
    RuleAssignment,
    ValidationResult,
    ValidationStatus,
)
from src.metadata.repository import MetadataRepository
from src.rules.multi_field import MultiFieldValidator
from src.rules.single_field import SingleFieldValidator
from src.utils.exceptions import RuleExecutionException
from src.utils.logger import get_logger
from src.utils.metrics import get_metrics_collector


class RuleExecutor:
    """Main executor for validation rules."""

    def __init__(
        self,
        metadata_repository: MetadataRepository,
        spark_session: Optional[SparkSession] = None,
    ):
        """
        Initialize rule executor.

        Args:
            metadata_repository: Metadata repository instance
            spark_session: Optional Spark session (created if not provided)
        """
        self.metadata_repo = metadata_repository
        self.logger = get_logger(self.__class__.__name__)
        self.metrics = get_metrics_collector()

        # Initialize Spark session if not provided
        if spark_session:
            self.spark_session = spark_session
        else:
            self.spark_session = SparkSession.builder.appName(
                "RulesEngine"
            ).getOrCreate()

        # Initialize validators
        self.single_field_validator = SingleFieldValidator()
        self.multi_field_validator = MultiFieldValidator()

    def execute_assignment(
        self,
        assignment_id: UUID,
        execution_id: Optional[UUID] = None,
        sample_size: int = 100,
    ) -> ValidationResult:
        """
        Execute validation for a rule assignment.

        Args:
            assignment_id: Rule assignment ID
            execution_id: Optional execution ID (created if not provided)
            sample_size: Number of failed records to sample

        Returns:
            ValidationResult model

        Raises:
            RuleExecutionException: If execution fails
        """
        execution_id = execution_id or uuid4()
        start_time = time.time()

        try:
            self.logger.info(
                "Starting rule execution",
                assignment_id=str(assignment_id),
                execution_id=str(execution_id),
            )

            # Load assignment and rule metadata
            assignment = self.metadata_repo.get_assignment(assignment_id)
            if not assignment:
                raise RuleExecutionException(f"Assignment not found: {assignment_id}")

            if not assignment.is_active:
                raise RuleExecutionException(f"Assignment is not active: {assignment_id}")

            rule = self.metadata_repo.get_rule(assignment.rule_id)
            if not rule:
                raise RuleExecutionException(f"Rule not found: {assignment.rule_id}")

            if not rule.is_active:
                raise RuleExecutionException(f"Rule is not active: {assignment.rule_id}")

            # Load data source
            data_source = self.metadata_repo.get_data_source(assignment.source_id)
            if not data_source:
                raise RuleExecutionException(f"Data source not found: {assignment.source_id}")

            # Create connector
            connector = ConnectorFactory.create_connector(
                data_source.source_type,
                data_source.connection_config,
                self.spark_session,
            )

            # Create execution log
            from datetime import datetime
            execution_log = ExecutionLog(
                execution_id=execution_id,
                execution_type=assignment.execution_frequency.value,
                source_id=assignment.source_id,
                assignment_id=assignment_id,
                start_time=datetime.utcnow(),
                status=ExecutionStatus.RUNNING,
            )
            self.metadata_repo.create_execution_log(execution_log)

            # Read data
            with connector:
                connector.connect()
                dataframe = connector.read_data(
                    table=assignment.table_name,
                    schema=assignment.schema_name,
                    columns=assignment.column_names,
                )

                # Execute validation based on rule type
                if rule.rule_type.value == "single_field":
                    if len(assignment.column_names) != 1:
                        raise RuleExecutionException(
                            "Single-field rule requires exactly one column"
                        )
                    validation_result = self.single_field_validator.validate(
                        dataframe, rule, assignment.column_names[0], sample_size
                    )
                elif rule.rule_type.value == "multi_field":
                    validation_result = self.multi_field_validator.validate(
                        dataframe, rule, assignment.column_names, sample_size
                    )
                else:
                    raise RuleExecutionException(
                        f"Unsupported rule type: {rule.rule_type.value}"
                    )

            # Calculate execution duration
            execution_duration_ms = int((time.time() - start_time) * 1000)

            # Create validation result model
            result = ValidationResult(
                rule_id=rule.rule_id,
                assignment_id=assignment_id,
                execution_id=execution_id,
                records_checked=validation_result["records_checked"],
                records_failed=validation_result["records_failed"],
                records_passed=validation_result["records_passed"],
                failure_rate=validation_result["failure_rate"],
                failure_details=validation_result.get("failure_details"),
                status=ValidationStatus(validation_result["status"]),
                execution_duration_ms=execution_duration_ms,
                sample_failed_records=validation_result.get("sample_failed_records"),
            )

            # Save result
            result_id = self.metadata_repo.save_validation_result(result)

            # Update execution log
            from datetime import datetime
            self.metadata_repo.update_execution_log(
                execution_id=execution_id,
                status=ExecutionStatus.COMPLETED.value,
                end_time=datetime.utcnow(),
                records_processed=validation_result["records_checked"],
            )

            # Record metrics
            self.metrics.record_validation_result(
                rule_id=str(rule.rule_id),
                assignment_id=str(assignment_id),
                status=validation_result["status"],
                records_checked=validation_result["records_checked"],
                records_failed=validation_result["records_failed"],
                duration_ms=execution_duration_ms,
                source_id=str(assignment.source_id),
            )

            self.logger.info(
                "Rule execution completed",
                assignment_id=str(assignment_id),
                execution_id=str(execution_id),
                status=validation_result["status"],
                records_checked=validation_result["records_checked"],
                records_failed=validation_result["records_failed"],
            )

            return result

        except Exception as e:
            # Update execution log with error
            if execution_id:
                from datetime import datetime
                self.metadata_repo.update_execution_log(
                    execution_id=execution_id,
                    status=ExecutionStatus.FAILED.value,
                    end_time=datetime.utcnow(),
                    error_message=str(e),
                )

            self.logger.exception(
                "Rule execution failed",
                assignment_id=str(assignment_id),
                execution_id=str(execution_id),
                error=str(e),
            )
            raise RuleExecutionException(f"Rule execution failed: {str(e)}") from e

    def execute_batch(
        self,
        assignment_ids: List[UUID],
        execution_id: Optional[UUID] = None,
        max_parallel: int = 5,
    ) -> List[ValidationResult]:
        """
        Execute multiple rule assignments in batch.

        Args:
            assignment_ids: List of assignment IDs
            execution_id: Optional execution ID (created if not provided)
            max_parallel: Maximum parallel executions (not yet implemented)

        Returns:
            List of ValidationResult models
        """
        execution_id = execution_id or uuid4()
        results = []

        self.logger.info(
            "Starting batch execution",
            execution_id=str(execution_id),
            assignment_count=len(assignment_ids),
        )

        for assignment_id in assignment_ids:
            try:
                result = self.execute_assignment(assignment_id, execution_id)
                results.append(result)
            except Exception as e:
                self.logger.error(
                    "Assignment execution failed in batch",
                    assignment_id=str(assignment_id),
                    error=str(e),
                )
                # Continue with other assignments
                continue

        self.logger.info(
            "Batch execution completed",
            execution_id=str(execution_id),
            successful=len(results),
            total=len(assignment_ids),
        )

        return results

    def load_rules_metadata(self, assignment_id: UUID) -> tuple[RuleAssignment, Any]:
        """
        Load rules metadata for an assignment.

        Args:
            assignment_id: Assignment ID

        Returns:
            Tuple of (RuleAssignment, ValidationRule)
        """
        assignment = self.metadata_repo.get_assignment(assignment_id)
        if not assignment:
            raise RuleExecutionException(f"Assignment not found: {assignment_id}")

        rule = self.metadata_repo.get_rule(assignment.rule_id)
        if not rule:
            raise RuleExecutionException(f"Rule not found: {assignment.rule_id}")

        return assignment, rule
