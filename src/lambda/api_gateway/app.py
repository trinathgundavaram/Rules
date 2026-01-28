"""FastAPI application for API Gateway Lambda function."""

import json
import os
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.metadata.models import (
    DataSource,
    ExecutionLog,
    RuleAssignment,
    ValidationResult,
    ValidationRule,
)
from src.metadata.repository import MetadataRepository
from src.rules.executor import RuleExecutor
from src.utils.logger import get_logger

# Initialize FastAPI app
app = FastAPI(title="Rules Engine API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize logger
logger = get_logger(__name__)

# Global repository instance (initialized on first request)
_metadata_repo: Optional[MetadataRepository] = None
_executor: Optional[RuleExecutor] = None


def get_repository() -> MetadataRepository:
    """Get or create metadata repository instance."""
    global _metadata_repo
    if _metadata_repo is None:
        db_host = os.environ.get("METADATA_DB_HOST")
        db_port = int(os.environ.get("METADATA_DB_PORT", 5432))
        db_name = os.environ.get("METADATA_DB_NAME")
        db_user = os.environ.get("METADATA_DB_USER")
        db_password = os.environ.get("METADATA_DB_PASSWORD")

        if not all([db_host, db_name, db_user, db_password]):
            raise ValueError("Database configuration missing")

        _metadata_repo = MetadataRepository(
            host=db_host,
            port=db_port,
            database=db_name,
            username=db_user,
            password=db_password,
        )
    return _metadata_repo


def get_executor() -> RuleExecutor:
    """Get or create rule executor instance."""
    global _executor
    if _executor is None:
        _executor = RuleExecutor(get_repository())
    return _executor


# ========================================================================
# Pydantic Models for API Requests/Responses
# ========================================================================

class CreateRuleRequest(BaseModel):
    """Request model for creating a rule."""

    rule_name: str
    rule_type: str
    rule_category: str
    severity_level: str
    rule_logic: str
    threshold_value: Optional[float] = None
    is_reusable: bool = True
    description: Optional[str] = None
    created_by: str


class CreateDataSourceRequest(BaseModel):
    """Request model for creating a data source."""

    source_name: str
    source_type: str
    connection_config: dict
    description: Optional[str] = None
    created_by: str


class CreateAssignmentRequest(BaseModel):
    """Request model for creating a rule assignment."""

    rule_id: str
    source_id: str
    schema_name: str
    table_name: str
    column_names: List[str]
    execution_frequency: str
    schedule_expression: Optional[str] = None
    priority_order: int = 0
    created_by: str


class ExecuteValidationRequest(BaseModel):
    """Request model for executing validation."""

    assignment_id: str
    trigger_glue: bool = False


# ========================================================================
# API Endpoints
# ========================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Rules Engine API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        repo = get_repository()
        # Simple connection test
        repo.list_data_sources(limit=1)
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


# Rules endpoints
@app.post("/api/rules", response_model=dict)
async def create_rule(request: CreateRuleRequest):
    """Create a new validation rule."""
    try:
        repo = get_repository()
        rule = ValidationRule(
            rule_name=request.rule_name,
            rule_type=request.rule_type,
            rule_category=request.rule_category,
            severity_level=request.severity_level,
            rule_logic=request.rule_logic,
            threshold_value=request.threshold_value,
            is_reusable=request.is_reusable,
            description=request.description,
            created_by=request.created_by,
        )
        rule_id = repo.create_rule(rule)
        return {"rule_id": str(rule_id), "message": "Rule created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/rules", response_model=List[dict])
async def list_rules(
    rule_type: Optional[str] = None,
    rule_category: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """List validation rules."""
    try:
        repo = get_repository()
        rules = repo.list_rules(rule_type, rule_category, is_active)
        return [rule.dict() for rule in rules]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rules/{rule_id}", response_model=dict)
async def get_rule(rule_id: str):
    """Get a validation rule by ID."""
    try:
        repo = get_repository()
        rule = repo.get_rule(UUID(rule_id))
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return rule.dict()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Data source endpoints
@app.post("/api/data-sources", response_model=dict)
async def create_data_source(request: CreateDataSourceRequest):
    """Create a new data source."""
    try:
        repo = get_repository()
        data_source = DataSource(
            source_name=request.source_name,
            source_type=request.source_type,
            connection_config=request.connection_config,
            description=request.description,
            created_by=request.created_by,
        )
        source_id = repo.create_data_source(data_source)
        return {"source_id": str(source_id), "message": "Data source created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/data-sources", response_model=List[dict])
async def list_data_sources(is_active: Optional[bool] = None):
    """List data sources."""
    try:
        repo = get_repository()
        sources = repo.list_data_sources(is_active)
        return [source.dict() for source in sources]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Assignment endpoints
@app.post("/api/assignments", response_model=dict)
async def create_assignment(request: CreateAssignmentRequest):
    """Create a new rule assignment."""
    try:
        repo = get_repository()
        assignment = RuleAssignment(
            rule_id=UUID(request.rule_id),
            source_id=UUID(request.source_id),
            schema_name=request.schema_name,
            table_name=request.table_name,
            column_names=request.column_names,
            execution_frequency=request.execution_frequency,
            schedule_expression=request.schedule_expression,
            priority_order=request.priority_order,
            created_by=request.created_by,
        )
        assignment_id = repo.assign_rule(assignment)
        return {
            "assignment_id": str(assignment_id),
            "message": "Assignment created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/assignments", response_model=List[dict])
async def list_assignments(
    source_id: Optional[str] = None,
    rule_id: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """List rule assignments."""
    try:
        repo = get_repository()
        source_uuid = UUID(source_id) if source_id else None
        rule_uuid = UUID(rule_id) if rule_id else None
        assignments = repo.list_assignments(source_uuid, rule_uuid, is_active)
        return [assignment.dict() for assignment in assignments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Validation execution endpoints
@app.post("/api/validations/execute", response_model=dict)
async def execute_validation(request: ExecuteValidationRequest):
    """Execute a validation."""
    try:
        executor = get_executor()
        result = executor.execute_assignment(UUID(request.assignment_id))
        return {
            "result_id": str(result.result_id),
            "status": result.status.value,
            "records_checked": result.records_checked,
            "records_failed": result.records_failed,
            "message": "Validation completed",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/validations/results", response_model=List[dict])
async def get_validation_results(
    rule_id: Optional[str] = None,
    assignment_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
):
    """Get validation results."""
    try:
        repo = get_repository()
        rule_uuid = UUID(rule_id) if rule_id else None
        assignment_uuid = UUID(assignment_id) if assignment_id else None
        execution_uuid = UUID(execution_id) if execution_id else None

        results = repo.get_validation_results(
            rule_uuid, assignment_uuid, execution_uuid, status, limit
        )
        return [result.dict() for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Lambda handler for API Gateway
def lambda_handler(event: dict, context: Any) -> dict:
    """
    Lambda handler for API Gateway.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    from mangum import Mangum

    handler = Mangum(app)
    return handler(event, context)
