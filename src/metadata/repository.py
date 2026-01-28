"""Metadata repository for database operations."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from src.metadata.models import (
    DataSource,
    ExecutionLog,
    QualityScore,
    RuleAssignment,
    ValidationResult,
    ValidationRule,
)
from src.utils.exceptions import MetadataException
from src.utils.logger import get_logger


class MetadataRepository:
    """Repository for metadata database operations."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        host: Optional[str] = None,
        port: int = 5432,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
    ):
        """
        Initialize metadata repository.

        Args:
            connection_string: Full PostgreSQL connection string
            host: Database host (if not using connection_string)
            port: Database port
            database: Database name
            username: Database username
            password: Database password
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
        """
        self.logger = get_logger(self.__class__.__name__)

        if connection_string:
            self.connection_string = connection_string
        else:
            if not all([host, database, username, password]):
                raise MetadataException(
                    "Either connection_string or all connection parameters must be provided"
                )
            self.connection_string = (
                f"postgresql://{username}:{password}@{host}:{port}/{database}"
            )

        try:
            self.engine: Engine = create_engine(
                self.connection_string,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,  # Verify connections before using
            )
            self.logger.info("Initialized metadata repository connection pool")
        except Exception as e:
            raise MetadataException(f"Failed to initialize database connection: {str(e)}") from e

    # ========================================================================
    # DATA SOURCE OPERATIONS
    # ========================================================================

    def create_data_source(self, data_source: DataSource) -> UUID:
        """
        Create a new data source.

        Args:
            data_source: DataSource model instance

        Returns:
            Created source_id
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        INSERT INTO data_sources 
                        (source_name, source_type, connection_config, is_active, created_by, description)
                        VALUES (:source_name, :source_type, :connection_config::jsonb, :is_active, :created_by, :description)
                        RETURNING source_id
                    """),
                    {
                        "source_name": data_source.source_name,
                        "source_type": data_source.source_type.value,
                        "connection_config": json.dumps(data_source.connection_config),
                        "is_active": data_source.is_active,
                        "created_by": data_source.created_by,
                        "description": data_source.description,
                    },
                )
                source_id = result.scalar()
                conn.commit()
                self.logger.info("Created data source", source_id=str(source_id))
                return source_id
        except Exception as e:
            raise MetadataException(f"Failed to create data source: {str(e)}") from e

    def get_data_source(self, source_id: UUID) -> Optional[DataSource]:
        """
        Get data source by ID.

        Args:
            source_id: Source identifier

        Returns:
            DataSource model or None if not found
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM data_sources WHERE source_id = :source_id"),
                    {"source_id": str(source_id)},
                )
                row = result.fetchone()
                if not row:
                    return None

                return DataSource(
                    source_id=row.source_id,
                    source_name=row.source_name,
                    source_type=row.source_type,
                    connection_config=row.connection_config,
                    is_active=row.is_active,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    created_by=row.created_by,
                    updated_by=row.updated_by,
                    description=row.description,
                )
        except Exception as e:
            raise MetadataException(f"Failed to get data source: {str(e)}") from e

    def list_data_sources(self, is_active: Optional[bool] = None) -> List[DataSource]:
        """
        List all data sources.

        Args:
            is_active: Filter by active status (optional)

        Returns:
            List of DataSource models
        """
        try:
            with self.engine.connect() as conn:
                query = "SELECT * FROM data_sources"
                params = {}
                if is_active is not None:
                    query += " WHERE is_active = :is_active"
                    params["is_active"] = is_active

                result = conn.execute(text(query), params)
                return [
                    DataSource(
                        source_id=row.source_id,
                        source_name=row.source_name,
                        source_type=row.source_type,
                        connection_config=row.connection_config,
                        is_active=row.is_active,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        created_by=row.created_by,
                        updated_by=row.updated_by,
                        description=row.description,
                    )
                    for row in result
                ]
        except Exception as e:
            raise MetadataException(f"Failed to list data sources: {str(e)}") from e

    # ========================================================================
    # VALIDATION RULE OPERATIONS
    # ========================================================================

    def create_rule(self, rule: ValidationRule) -> UUID:
        """
        Create a new validation rule.

        Args:
            rule: ValidationRule model instance

        Returns:
            Created rule_id
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        INSERT INTO validation_rules
                        (rule_name, rule_type, rule_category, severity_level, rule_logic,
                         threshold_value, is_reusable, description, created_by, version, is_active)
                        VALUES (:rule_name, :rule_type, :rule_category, :severity_level, :rule_logic,
                                :threshold_value, :is_reusable, :description, :created_by, :version, :is_active)
                        RETURNING rule_id
                    """),
                    {
                        "rule_name": rule.rule_name,
                        "rule_type": rule.rule_type.value,
                        "rule_category": rule.rule_category.value,
                        "severity_level": rule.severity_level.value,
                        "rule_logic": rule.rule_logic,
                        "threshold_value": rule.threshold_value,
                        "is_reusable": rule.is_reusable,
                        "description": rule.description,
                        "created_by": rule.created_by,
                        "version": rule.version,
                        "is_active": rule.is_active,
                    },
                )
                rule_id = result.scalar()
                conn.commit()

                # Create version history entry
                conn.execute(
                    text("""
                        INSERT INTO rule_version_history
                        (rule_id, version_number, rule_name, rule_logic, changed_by, is_current_version)
                        VALUES (:rule_id, :version_number, :rule_name, :rule_logic, :changed_by, TRUE)
                    """),
                    {
                        "rule_id": rule_id,
                        "version_number": rule.version,
                        "rule_name": rule.rule_name,
                        "rule_logic": rule.rule_logic,
                        "changed_by": rule.created_by,
                    },
                )
                conn.commit()

                self.logger.info("Created validation rule", rule_id=str(rule_id))
                return rule_id
        except Exception as e:
            raise MetadataException(f"Failed to create rule: {str(e)}") from e

    def get_rule(self, rule_id: UUID) -> Optional[ValidationRule]:
        """
        Get validation rule by ID.

        Args:
            rule_id: Rule identifier

        Returns:
            ValidationRule model or None if not found
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM validation_rules WHERE rule_id = :rule_id"),
                    {"rule_id": str(rule_id)},
                )
                row = result.fetchone()
                if not row:
                    return None

                return ValidationRule(
                    rule_id=row.rule_id,
                    rule_name=row.rule_name,
                    rule_type=row.rule_type,
                    rule_category=row.rule_category,
                    severity_level=row.severity_level,
                    rule_logic=row.rule_logic,
                    threshold_value=float(row.threshold_value) if row.threshold_value else None,
                    is_reusable=row.is_reusable,
                    description=row.description,
                    created_by=row.created_by,
                    created_at=row.created_at,
                    updated_by=row.updated_by,
                    updated_at=row.updated_at,
                    version=row.version,
                    is_active=row.is_active,
                )
        except Exception as e:
            raise MetadataException(f"Failed to get rule: {str(e)}") from e

    def list_rules(
        self,
        rule_type: Optional[str] = None,
        rule_category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[ValidationRule]:
        """
        List validation rules with optional filters.

        Args:
            rule_type: Filter by rule type
            rule_category: Filter by rule category
            is_active: Filter by active status

        Returns:
            List of ValidationRule models
        """
        try:
            with self.engine.connect() as conn:
                query = "SELECT * FROM validation_rules WHERE 1=1"
                params = {}

                if rule_type:
                    query += " AND rule_type = :rule_type"
                    params["rule_type"] = rule_type
                if rule_category:
                    query += " AND rule_category = :rule_category"
                    params["rule_category"] = rule_category
                if is_active is not None:
                    query += " AND is_active = :is_active"
                    params["is_active"] = is_active

                result = conn.execute(text(query), params)
                return [
                    ValidationRule(
                        rule_id=row.rule_id,
                        rule_name=row.rule_name,
                        rule_type=row.rule_type,
                        rule_category=row.rule_category,
                        severity_level=row.severity_level,
                        rule_logic=row.rule_logic,
                        threshold_value=float(row.threshold_value) if row.threshold_value else None,
                        is_reusable=row.is_reusable,
                        description=row.description,
                        created_by=row.created_by,
                        created_at=row.created_at,
                        updated_by=row.updated_by,
                        updated_at=row.updated_at,
                        version=row.version,
                        is_active=row.is_active,
                    )
                    for row in result
                ]
        except Exception as e:
            raise MetadataException(f"Failed to list rules: {str(e)}") from e

    # ========================================================================
    # RULE ASSIGNMENT OPERATIONS
    # ========================================================================

    def assign_rule(self, assignment: RuleAssignment) -> UUID:
        """
        Assign a rule to a table/columns.

        Args:
            assignment: RuleAssignment model instance

        Returns:
            Created assignment_id
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        INSERT INTO rule_assignments
                        (rule_id, source_id, schema_name, table_name, column_names,
                         execution_frequency, schedule_expression, is_active, priority_order,
                         created_by, additional_config)
                        VALUES (:rule_id, :source_id, :schema_name, :table_name, :column_names::jsonb,
                                :execution_frequency, :schedule_expression, :is_active, :priority_order,
                                :created_by, :additional_config::jsonb)
                        RETURNING assignment_id
                    """),
                    {
                        "rule_id": str(assignment.rule_id),
                        "source_id": str(assignment.source_id),
                        "schema_name": assignment.schema_name,
                        "table_name": assignment.table_name,
                        "column_names": json.dumps(assignment.column_names),
                        "execution_frequency": assignment.execution_frequency.value,
                        "schedule_expression": assignment.schedule_expression,
                        "is_active": assignment.is_active,
                        "priority_order": assignment.priority_order,
                        "created_by": assignment.created_by,
                        "additional_config": json.dumps(assignment.additional_config) if assignment.additional_config else None,
                    },
                )
                assignment_id = result.scalar()
                conn.commit()
                self.logger.info("Created rule assignment", assignment_id=str(assignment_id))
                return assignment_id
        except Exception as e:
            raise MetadataException(f"Failed to assign rule: {str(e)}") from e

    def get_assignment(self, assignment_id: UUID) -> Optional[RuleAssignment]:
        """
        Get rule assignment by ID.

        Args:
            assignment_id: Assignment identifier

        Returns:
            RuleAssignment model or None if not found
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM rule_assignments WHERE assignment_id = :assignment_id"),
                    {"assignment_id": str(assignment_id)},
                )
                row = result.fetchone()
                if not row:
                    return None

                return RuleAssignment(
                    assignment_id=row.assignment_id,
                    rule_id=row.rule_id,
                    source_id=row.source_id,
                    schema_name=row.schema_name,
                    table_name=row.table_name,
                    column_names=row.column_names,
                    execution_frequency=row.execution_frequency,
                    schedule_expression=row.schedule_expression,
                    is_active=row.is_active,
                    priority_order=row.priority_order,
                    created_by=row.created_by,
                    created_at=row.created_at,
                    updated_by=row.updated_by,
                    updated_at=row.updated_at,
                    additional_config=row.additional_config,
                )
        except Exception as e:
            raise MetadataException(f"Failed to get assignment: {str(e)}") from e

    def list_assignments(
        self,
        source_id: Optional[UUID] = None,
        rule_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> List[RuleAssignment]:
        """
        List rule assignments with optional filters.

        Args:
            source_id: Filter by source ID
            rule_id: Filter by rule ID
            is_active: Filter by active status

        Returns:
            List of RuleAssignment models
        """
        try:
            with self.engine.connect() as conn:
                query = "SELECT * FROM rule_assignments WHERE 1=1"
                params = {}

                if source_id:
                    query += " AND source_id = :source_id"
                    params["source_id"] = str(source_id)
                if rule_id:
                    query += " AND rule_id = :rule_id"
                    params["rule_id"] = str(rule_id)
                if is_active is not None:
                    query += " AND is_active = :is_active"
                    params["is_active"] = is_active

                query += " ORDER BY priority_order, created_at DESC"

                result = conn.execute(text(query), params)
                return [
                    RuleAssignment(
                        assignment_id=row.assignment_id,
                        rule_id=row.rule_id,
                        source_id=row.source_id,
                        schema_name=row.schema_name,
                        table_name=row.table_name,
                        column_names=row.column_names,
                        execution_frequency=row.execution_frequency,
                        schedule_expression=row.schedule_expression,
                        is_active=row.is_active,
                        priority_order=row.priority_order,
                        created_by=row.created_by,
                        created_at=row.created_at,
                        updated_by=row.updated_by,
                        updated_at=row.updated_at,
                        additional_config=row.additional_config,
                    )
                    for row in result
                ]
        except Exception as e:
            raise MetadataException(f"Failed to list assignments: {str(e)}") from e

    # ========================================================================
    # VALIDATION RESULT OPERATIONS
    # ========================================================================

    def save_validation_result(self, result: ValidationResult) -> UUID:
        """
        Save validation result.

        Args:
            result: ValidationResult model instance

        Returns:
            Created result_id
        """
        try:
            with self.engine.connect() as conn:
                # Calculate failure rate if not provided
                if result.failure_rate is None:
                    result.failure_rate = result.calculate_failure_rate()

                result_id = result.result_id or uuid4()
                conn.execute(
                    text("""
                        INSERT INTO validation_results
                        (result_id, rule_id, assignment_id, execution_id, validation_timestamp,
                         records_checked, records_failed, records_passed, failure_rate,
                         failure_details, status, execution_duration_ms, error_message,
                         sample_failed_records, metadata)
                        VALUES (:result_id, :rule_id, :assignment_id, :execution_id, :validation_timestamp,
                                :records_checked, :records_failed, :records_passed, :failure_rate,
                                :failure_details::jsonb, :status, :execution_duration_ms, :error_message,
                                :sample_failed_records::jsonb, :metadata::jsonb)
                    """),
                    {
                        "result_id": str(result_id),
                        "rule_id": str(result.rule_id),
                        "assignment_id": str(result.assignment_id),
                        "execution_id": str(result.execution_id),
                        "validation_timestamp": result.validation_timestamp or datetime.utcnow(),
                        "records_checked": result.records_checked,
                        "records_failed": result.records_failed,
                        "records_passed": result.records_passed,
                        "failure_rate": result.failure_rate,
                        "failure_details": json.dumps(result.failure_details) if result.failure_details else None,
                        "status": result.status.value,
                        "execution_duration_ms": result.execution_duration_ms,
                        "error_message": result.error_message,
                        "sample_failed_records": json.dumps(result.sample_failed_records) if result.sample_failed_records else None,
                        "metadata": json.dumps(result.metadata) if result.metadata else None,
                    },
                )
                conn.commit()
                self.logger.info("Saved validation result", result_id=str(result_id))
                return result_id
        except Exception as e:
            raise MetadataException(f"Failed to save validation result: {str(e)}") from e

    def get_validation_results(
        self,
        rule_id: Optional[UUID] = None,
        assignment_id: Optional[UUID] = None,
        execution_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[ValidationResult]:
        """
        Get validation results with optional filters.

        Args:
            rule_id: Filter by rule ID
            assignment_id: Filter by assignment ID
            execution_id: Filter by execution ID
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of ValidationResult models
        """
        try:
            with self.engine.connect() as conn:
                query = "SELECT * FROM validation_results WHERE 1=1"
                params = {}

                if rule_id:
                    query += " AND rule_id = :rule_id"
                    params["rule_id"] = str(rule_id)
                if assignment_id:
                    query += " AND assignment_id = :assignment_id"
                    params["assignment_id"] = str(assignment_id)
                if execution_id:
                    query += " AND execution_id = :execution_id"
                    params["execution_id"] = str(execution_id)
                if status:
                    query += " AND status = :status"
                    params["status"] = status

                query += " ORDER BY validation_timestamp DESC LIMIT :limit"
                params["limit"] = limit

                result = conn.execute(text(query), params)
                return [
                    ValidationResult(
                        result_id=row.result_id,
                        rule_id=row.rule_id,
                        assignment_id=row.assignment_id,
                        execution_id=row.execution_id,
                        validation_timestamp=row.validation_timestamp,
                        records_checked=row.records_checked,
                        records_failed=row.records_failed,
                        records_passed=row.records_passed,
                        failure_rate=float(row.failure_rate) if row.failure_rate else None,
                        failure_details=row.failure_details,
                        status=row.status,
                        execution_duration_ms=row.execution_duration_ms,
                        error_message=row.error_message,
                        sample_failed_records=row.sample_failed_records,
                        metadata=row.metadata,
                    )
                    for row in result
                ]
        except Exception as e:
            raise MetadataException(f"Failed to get validation results: {str(e)}") from e

    # ========================================================================
    # EXECUTION LOG OPERATIONS
    # ========================================================================

    def create_execution_log(self, log: ExecutionLog) -> UUID:
        """
        Create execution log entry.

        Args:
            log: ExecutionLog model instance

        Returns:
            Created log_id
        """
        try:
            with self.engine.connect() as conn:
                log_id = log.log_id or uuid4()
                conn.execute(
                    text("""
                        INSERT INTO execution_logs
                        (log_id, execution_id, execution_type, source_id, assignment_id,
                         start_time, end_time, status, error_message, error_stack_trace,
                         records_processed, execution_duration_ms, metadata)
                        VALUES (:log_id, :execution_id, :execution_type, :source_id, :assignment_id,
                                :start_time, :end_time, :status, :error_message, :error_stack_trace,
                                :records_processed, :execution_duration_ms, :metadata::jsonb)
                    """),
                    {
                        "log_id": str(log_id),
                        "execution_id": str(log.execution_id),
                        "execution_type": log.execution_type,
                        "source_id": str(log.source_id) if log.source_id else None,
                        "assignment_id": str(log.assignment_id) if log.assignment_id else None,
                        "start_time": log.start_time,
                        "end_time": log.end_time,
                        "status": log.status.value,
                        "error_message": log.error_message,
                        "error_stack_trace": log.error_stack_trace,
                        "records_processed": log.records_processed,
                        "execution_duration_ms": log.execution_duration_ms or log.calculate_duration_ms(),
                        "metadata": json.dumps(log.metadata) if log.metadata else None,
                    },
                )
                conn.commit()
                self.logger.info("Created execution log", log_id=str(log_id))
                return log_id
        except Exception as e:
            raise MetadataException(f"Failed to create execution log: {str(e)}") from e

    def update_execution_log(
        self,
        execution_id: UUID,
        status: Optional[str] = None,
        end_time: Optional[datetime] = None,
        error_message: Optional[str] = None,
        records_processed: Optional[int] = None,
    ) -> None:
        """
        Update execution log.

        Args:
            execution_id: Execution identifier
            status: New status
            end_time: End time
            error_message: Error message
            records_processed: Records processed count
        """
        try:
            with self.engine.connect() as conn:
                updates = []
                params = {"execution_id": str(execution_id)}

                if status:
                    updates.append("status = :status")
                    params["status"] = status
                if end_time:
                    updates.append("end_time = :end_time")
                    params["end_time"] = end_time
                if error_message:
                    updates.append("error_message = :error_message")
                    params["error_message"] = error_message
                if records_processed is not None:
                    updates.append("records_processed = :records_processed")
                    params["records_processed"] = records_processed

                if updates:
                    # Calculate duration if end_time is set
                    if end_time:
                        updates.append(
                            "execution_duration_ms = EXTRACT(EPOCH FROM (:end_time - start_time)) * 1000"
                        )

                    query = f"UPDATE execution_logs SET {', '.join(updates)} WHERE execution_id = :execution_id"
                    conn.execute(text(query), params)
                    conn.commit()
                    self.logger.info("Updated execution log", execution_id=str(execution_id))
        except Exception as e:
            raise MetadataException(f"Failed to update execution log: {str(e)}") from e
