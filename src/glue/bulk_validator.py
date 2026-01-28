"""AWS Glue job for bulk validation processing."""

import sys
from typing import Any, Dict
from uuid import UUID

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

from src.metadata.repository import MetadataRepository
from src.rules.executor import RuleExecutor
from src.utils.logger import get_logger

# Initialize Glue context
args = getResolvedOptions(sys.argv, ["JOB_NAME", "assignment_id", "execution_id"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

logger = get_logger(__name__)


def main():
    """Main Glue job function."""
    try:
        logger.info("Starting Glue bulk validation job", args=args)

        # Get parameters
        assignment_id_str = args.get("assignment_id")
        execution_id_str = args.get("execution_id")

        if not assignment_id_str:
            raise ValueError("assignment_id is required")

        assignment_id = UUID(assignment_id_str)
        execution_id = UUID(execution_id_str) if execution_id_str else None

        # Get database configuration from Glue connection or environment
        # In production, these would come from Glue connections or Parameter Store
        db_host = args.get("METADATA_DB_HOST")
        db_port = int(args.get("METADATA_DB_PORT", 5432))
        db_name = args.get("METADATA_DB_NAME")
        db_user = args.get("METADATA_DB_USER")
        db_password = args.get("METADATA_DB_PASSWORD")

        if not all([db_host, db_name, db_user, db_password]):
            raise ValueError("Database configuration missing")

        # Initialize repository
        metadata_repo = MetadataRepository(
            host=db_host,
            port=db_port,
            database=db_name,
            username=db_user,
            password=db_password,
        )

        # Initialize executor with Glue Spark session
        executor = RuleExecutor(metadata_repo, spark_session=spark)

        # Execute validation
        logger.info("Executing validation", assignment_id=assignment_id_str)
        result = executor.execute_assignment(assignment_id, execution_id)

        logger.info(
            "Bulk validation completed",
            assignment_id=assignment_id_str,
            result_id=str(result.result_id),
            status=result.status.value,
            records_checked=result.records_checked,
            records_failed=result.records_failed,
        )

        # Commit job
        job.commit()

        return {
            "status": "success",
            "result_id": str(result.result_id),
            "records_checked": result.records_checked,
            "records_failed": result.records_failed,
        }

    except Exception as e:
        logger.exception("Glue job failed", error=str(e))
        job.commit()  # Commit even on failure to mark job as complete
        raise


if __name__ == "__main__":
    main()
