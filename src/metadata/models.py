"""Pydantic models for metadata entities."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    """Supported data source types."""

    DATABRICKS = "databricks"
    SQL_SERVER = "sqlserver"
    TERADATA = "teradata"
    S3 = "s3"
    REDSHIFT = "redshift"
    AURORA_POSTGRESQL = "aurora_postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"


class RuleType(str, Enum):
    """Validation rule types."""

    SINGLE_FIELD = "single_field"
    MULTI_FIELD = "multi_field"
    CROSS_TABLE = "cross_table"


class RuleCategory(str, Enum):
    """Rule categories."""

    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    INTEGRITY = "integrity"
    TIMELINESS = "timeliness"
    CUSTOM = "custom"


class SeverityLevel(str, Enum):
    """Severity levels for rules."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExecutionFrequency(str, Enum):
    """Execution frequency types."""

    BATCH = "batch"
    STREAMING = "streaming"
    SCHEDULED = "scheduled"
    ON_DEMAND = "on_demand"


class ValidationStatus(str, Enum):
    """Validation result status."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    WARNING = "warning"


class ExecutionStatus(str, Enum):
    """Execution status."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class DataSource(BaseModel):
    """Data source model."""

    source_id: Optional[UUID] = None
    source_name: str = Field(..., min_length=1, max_length=255)
    source_type: SourceType
    connection_config: Dict[str, Any]
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    description: Optional[str] = None

    class Config:
        """Pydantic config."""

        use_enum_values = True


class ValidationRule(BaseModel):
    """Validation rule model."""

    rule_id: Optional[UUID] = None
    rule_name: str = Field(..., min_length=1, max_length=255)
    rule_type: RuleType
    rule_category: RuleCategory
    severity_level: SeverityLevel
    rule_logic: str = Field(..., min_length=1)
    threshold_value: Optional[float] = None
    is_reusable: bool = True
    description: Optional[str] = None
    created_by: str = Field(..., min_length=1)
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    version: int = 1
    is_active: bool = True

    class Config:
        """Pydantic config."""

        use_enum_values = True


class RuleAssignment(BaseModel):
    """Rule assignment model."""

    assignment_id: Optional[UUID] = None
    rule_id: UUID
    source_id: UUID
    schema_name: str = Field(..., min_length=1, max_length=255)
    table_name: str = Field(..., min_length=1, max_length=255)
    column_names: List[str] = Field(..., min_items=1)
    execution_frequency: ExecutionFrequency
    schedule_expression: Optional[str] = None
    is_active: bool = True
    priority_order: int = 0
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    additional_config: Optional[Dict[str, Any]] = None

    @field_validator("column_names")
    @classmethod
    def validate_column_names(cls, v: List[str]) -> List[str]:
        """Validate column names are not empty."""
        if not v or any(not col.strip() for col in v):
            raise ValueError("Column names must be non-empty")
        return v

    class Config:
        """Pydantic config."""

        use_enum_values = True


class ValidationResult(BaseModel):
    """Validation result model."""

    result_id: Optional[UUID] = None
    rule_id: UUID
    assignment_id: UUID
    execution_id: UUID
    validation_timestamp: Optional[datetime] = None
    records_checked: int = 0
    records_failed: int = 0
    records_passed: int = 0
    failure_rate: Optional[float] = None
    failure_details: Optional[Dict[str, Any]] = None
    status: ValidationStatus
    execution_duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    sample_failed_records: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

    def calculate_failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.records_checked == 0:
            return 0.0
        return (self.records_failed / self.records_checked) * 100

    class Config:
        """Pydantic config."""

        use_enum_values = True


class ExecutionLog(BaseModel):
    """Execution log model."""

    log_id: Optional[UUID] = None
    execution_id: UUID
    execution_type: str
    source_id: Optional[UUID] = None
    assignment_id: Optional[UUID] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    status: ExecutionStatus
    error_message: Optional[str] = None
    error_stack_trace: Optional[str] = None
    records_processed: int = 0
    execution_duration_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    def calculate_duration_ms(self) -> Optional[int]:
        """Calculate execution duration in milliseconds."""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() * 1000)
        return None

    class Config:
        """Pydantic config."""

        use_enum_values = True


class QualityScore(BaseModel):
    """Data quality score model."""

    score_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    schema_name: Optional[str] = None
    table_name: Optional[str] = None
    score_date: datetime
    overall_score: float = Field(..., ge=0, le=100)
    completeness_score: Optional[float] = Field(None, ge=0, le=100)
    accuracy_score: Optional[float] = Field(None, ge=0, le=100)
    consistency_score: Optional[float] = Field(None, ge=0, le=100)
    integrity_score: Optional[float] = Field(None, ge=0, le=100)
    timeliness_score: Optional[float] = Field(None, ge=0, le=100)
    total_rules_applied: int = 0
    rules_passed: int = 0
    rules_failed: int = 0
    calculated_at: Optional[datetime] = None
