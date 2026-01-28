"""Lambda handler for rule execution orchestration."""

import json
import os
from typing import Any, Dict
from uuid import UUID

import boto3

from src.metadata.repository import MetadataRepository
from src.rules.executor import RuleExecutor
from src.utils.logger import get_logger

# Initialize clients
glue_client = boto3.client("glue")
logger = get_logger(__name__)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for rule execution.

    Event structure:
    {
        "assignment_id": "uuid",
        "execution_type": "batch|scheduled|on_demand",
        "trigger_glue": true|false  # Whether to trigger Glue job for heavy processing
    }

    Args:
        event: Lambda event dictionary
        context: Lambda context

    Returns:
        Response dictionary
    """
    logger.info("Rule executor Lambda invoked", event=event)

    try:
        # Get configuration from environment
        db_host = os.environ.get("METADATA_DB_HOST")
        db_port = int(os.environ.get("METADATA_DB_PORT", 5432))
        db_name = os.environ.get("METADATA_DB_NAME")
        db_user = os.environ.get("METADATA_DB_USER")
        db_password = os.environ.get("METADATA_DB_PASSWORD")

        if not all([db_host, db_name, db_user, db_password]):
            raise ValueError("Database configuration missing from environment variables")

        # Initialize repository
        metadata_repo = MetadataRepository(
            host=db_host,
            port=db_port,
            database=db_name,
            username=db_user,
            password=db_password,
        )

        # Initialize executor
        executor = RuleExecutor(metadata_repo)

        # Get assignment ID from event
        assignment_id_str = event.get("assignment_id")
        if not assignment_id_str:
            raise ValueError("assignment_id is required in event")

        assignment_id = UUID(assignment_id_str)
        trigger_glue = event.get("trigger_glue", False)

        # Check if we should trigger Glue job for heavy processing
        if trigger_glue:
            logger.info("Triggering Glue job for heavy processing", assignment_id=assignment_id_str)
            glue_job_name = os.environ.get("GLUE_JOB_NAME", "rules-engine-bulk-validator")

            response = glue_client.start_job_run(
                JobName=glue_job_name,
                Arguments={
                    "--assignment_id": assignment_id_str,
                    "--execution_id": event.get("execution_id", ""),
                },
            )

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Glue job triggered",
                    "job_run_id": response["JobRunId"],
                    "assignment_id": assignment_id_str,
                }),
            }

        # Execute directly in Lambda (for lightweight validations)
        logger.info("Executing validation directly in Lambda", assignment_id=assignment_id_str)
        result = executor.execute_assignment(assignment_id)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Validation completed",
                "result_id": str(result.result_id),
                "status": result.status.value,
                "records_checked": result.records_checked,
                "records_failed": result.records_failed,
            }),
        }

    except Exception as e:
        logger.exception("Rule execution failed", error=str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "message": "Rule execution failed",
            }),
        }
