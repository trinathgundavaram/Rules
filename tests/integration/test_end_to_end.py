"""End-to-end integration tests."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from src.metadata.models import (
    DataSource,
    RuleAssignment,
    RuleCategory,
    RuleType,
    SeverityLevel,
    SourceType,
    ValidationRule,
)
from src.metadata.repository import MetadataRepository
from src.rules.executor import RuleExecutor


@pytest.mark.integration
class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock repository for testing."""
        repo = MagicMock(spec=MetadataRepository)
        
        # Mock data source
        source = DataSource(
            source_id=uuid4(),
            source_name="Test Source",
            source_type=SourceType.S3,
            connection_config={"bucket": "test"},
            created_by="test",
        )
        repo.get_data_source.return_value = source
        
        # Mock rule
        rule = ValidationRule(
            rule_id=uuid4(),
            rule_name="Email Check",
            rule_type=RuleType.SINGLE_FIELD,
            rule_category=RuleCategory.ACCURACY,
            severity_level=SeverityLevel.HIGH,
            rule_logic="is_email(col('email'))",
            created_by="test",
        )
        repo.get_rule.return_value = rule
        
        # Mock assignment
        assignment = RuleAssignment(
            assignment_id=uuid4(),
            rule_id=rule.rule_id,
            source_id=source.source_id,
            schema_name="public",
            table_name="users",
            column_names=["email"],
            execution_frequency="batch",
            created_by="test",
        )
        repo.get_assignment.return_value = assignment
        
        return repo

    @pytest.fixture
    def mock_connector(self, sample_spark_dataframe):
        """Create a mock connector."""
        connector = MagicMock()
        connector.connect = Mock()
        connector.disconnect = Mock()
        connector.read_data.return_value = sample_spark_dataframe
        connector.is_connected.return_value = True
        return connector

    def test_full_validation_workflow(
        self, mock_repo, mock_connector, sample_spark_dataframe, spark_session
    ):
        """Test complete validation workflow."""
        # Mock connector factory
        with patch("src.rules.executor.ConnectorFactory") as mock_factory:
            mock_factory.create_connector.return_value = mock_connector
            
            # Create executor
            executor = RuleExecutor(mock_repo, spark_session)
            
            # Execute validation
            assignment_id = uuid4()
            result = executor.execute_assignment(assignment_id)
            
            # Verify results
            assert result is not None
            assert result.records_checked == 4
            assert result.records_failed == 2  # Invalid email and null
            assert result.status.value in ["pass", "fail"]
            
            # Verify repository was called
            mock_repo.get_assignment.assert_called_once()
            mock_repo.get_rule.assert_called_once()
            mock_repo.get_data_source.assert_called_once()
            mock_repo.save_validation_result.assert_called_once()

    def test_batch_execution(self, mock_repo, mock_connector, spark_session):
        """Test batch execution of multiple assignments."""
        with patch("src.rules.executor.ConnectorFactory") as mock_factory:
            mock_factory.create_connector.return_value = mock_connector
            
            executor = RuleExecutor(mock_repo, spark_session)
            
            assignment_ids = [uuid4(), uuid4()]
            results = executor.execute_batch(assignment_ids)
            
            assert len(results) == 2
            assert all(r.records_checked > 0 for r in results)
