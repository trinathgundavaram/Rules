"""Metrics collection for CloudWatch integration."""

import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

try:
    import boto3
    from botocore.exceptions import ClientError

    CLOUDWATCH_AVAILABLE = True
except ImportError:
    CLOUDWATCH_AVAILABLE = False


class MetricsCollector:
    """Collects and publishes metrics to CloudWatch."""

    def __init__(
        self,
        namespace: str = "RulesEngine",
        region: Optional[str] = None,
        enabled: bool = True,
    ):
        """
        Initialize metrics collector.

        Args:
            namespace: CloudWatch namespace for metrics
            region: AWS region (defaults to boto3 default)
            enabled: Whether metrics collection is enabled
        """
        self.namespace = namespace
        self.enabled = enabled and CLOUDWATCH_AVAILABLE
        self.metrics_buffer: list[Dict[str, Any]] = []

        if self.enabled:
            self.client = boto3.client("cloudwatch", region_name=region)
        else:
            self.client = None

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Put a metric to CloudWatch.

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement (Count, Seconds, Bytes, etc.)
            dimensions: Optional dimensions for the metric
        """
        if not self.enabled:
            return

        metric_data = {
            "MetricName": metric_name,
            "Value": value,
            "Unit": unit,
        }

        if dimensions:
            metric_data["Dimensions"] = [
                {"Name": k, "Value": v} for k, v in dimensions.items()
            ]

        self.metrics_buffer.append(metric_data)

        # Flush if buffer is full (CloudWatch allows up to 20 metrics per request)
        if len(self.metrics_buffer) >= 20:
            self.flush()

    def flush(self) -> None:
        """Flush buffered metrics to CloudWatch."""
        if not self.enabled or not self.metrics_buffer:
            return

        try:
            self.client.put_metric_data(
                Namespace=self.namespace, MetricData=self.metrics_buffer
            )
            self.metrics_buffer.clear()
        except ClientError as e:
            # Log error but don't fail the operation
            print(f"Failed to publish metrics to CloudWatch: {e}")

    @contextmanager
    def timer(
        self,
        metric_name: str,
        dimensions: Optional[Dict[str, str]] = None,
    ):
        """
        Context manager for timing operations.

        Args:
            metric_name: Name of the metric
            dimensions: Optional dimensions

        Yields:
            None
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.put_metric(
                metric_name,
                duration,
                unit="Seconds",
                dimensions=dimensions,
            )

    def increment_counter(
        self,
        metric_name: str,
        value: float = 1.0,
        dimensions: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Increment a counter metric.

        Args:
            metric_name: Name of the metric
            value: Value to increment by (default 1.0)
            dimensions: Optional dimensions
        """
        self.put_metric(metric_name, value, unit="Count", dimensions=dimensions)

    def record_validation_result(
        self,
        rule_id: str,
        assignment_id: str,
        status: str,
        records_checked: int,
        records_failed: int,
        duration_ms: float,
        source_id: Optional[str] = None,
    ) -> None:
        """
        Record validation result metrics.

        Args:
            rule_id: Rule identifier
            assignment_id: Assignment identifier
            status: Validation status (pass/fail/error)
            records_checked: Number of records checked
            records_failed: Number of records that failed
            duration_ms: Execution duration in milliseconds
            source_id: Optional source identifier
        """
        dimensions = {
            "RuleId": rule_id,
            "AssignmentId": assignment_id,
            "Status": status,
        }
        if source_id:
            dimensions["SourceId"] = source_id

        # Record execution time
        self.put_metric(
            "ValidationDuration",
            duration_ms / 1000.0,  # Convert to seconds
            unit="Seconds",
            dimensions=dimensions,
        )

        # Record records checked
        self.put_metric(
            "RecordsChecked",
            records_checked,
            unit="Count",
            dimensions=dimensions,
        )

        # Record records failed
        self.put_metric(
            "RecordsFailed",
            records_failed,
            unit="Count",
            dimensions=dimensions,
        )

        # Record pass/fail status
        status_value = 1 if status == "pass" else 0
        self.put_metric(
            "ValidationStatus",
            status_value,
            unit="Count",
            dimensions=dimensions,
        )

        # Calculate and record failure rate
        if records_checked > 0:
            failure_rate = (records_failed / records_checked) * 100
            self.put_metric(
                "FailureRate",
                failure_rate,
                unit="Percent",
                dimensions=dimensions,
            )


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector(
    namespace: str = "RulesEngine",
    region: Optional[str] = None,
) -> MetricsCollector:
    """
    Get or create global metrics collector instance.

    Args:
        namespace: CloudWatch namespace
        region: AWS region

    Returns:
        Metrics collector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(namespace, region)
    return _metrics_collector
