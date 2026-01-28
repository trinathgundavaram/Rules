"""Tests for batch import utility."""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, Mock

from src.utils.batch_import import BatchRuleImporter
from src.utils.exceptions import MetadataException


class TestBatchRuleImporter:
    """Tests for BatchRuleImporter."""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock repository."""
        repo = MagicMock()
        repo.create_rule = Mock(return_value="rule-uuid-123")
        repo.assign_rule = Mock(return_value="assignment-uuid-456")
        repo.list_data_sources = Mock(return_value=[
            MagicMock(source_id="source-1", source_name="Test S3 Source")
        ])
        return repo

    def test_validate_csv_file(self, mock_repo):
        """Test CSV file validation."""
        importer = BatchRuleImporter(mock_repo)
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("rule_name,rule_type,rule_category,severity_level,rule_logic,created_by\n")
            f.write("Test Rule,single_field,accuracy,high,is_email(col('email')),admin\n")
            temp_path = f.name
        
        try:
            result = importer.validate_import_file(temp_path, "csv")
            assert result["valid"] is True
            assert result["total_rows"] == 1
        finally:
            os.unlink(temp_path)

    def test_validate_csv_missing_columns(self, mock_repo):
        """Test CSV validation with missing columns."""
        importer = BatchRuleImporter(mock_repo)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("rule_name,rule_type\n")  # Missing required columns
            f.write("Test Rule,single_field\n")
            temp_path = f.name
        
        try:
            result = importer.validate_import_file(temp_path, "csv")
            assert result["valid"] is False
            assert len(result["missing_columns"]) > 0
        finally:
            os.unlink(temp_path)

    def test_import_from_csv(self, mock_repo):
        """Test importing rules from CSV."""
        importer = BatchRuleImporter(mock_repo)
        
        csv_content = """rule_name,rule_type,rule_category,severity_level,rule_logic,created_by
Email Check,single_field,accuracy,high,is_email(col('email')),admin"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            result = importer.import_from_csv(temp_path, create_assignments=False)
            assert result["rules_created"] == 1
            assert result["errors"] == 0
            mock_repo.create_rule.assert_called_once()
        finally:
            os.unlink(temp_path)

    def test_import_with_assignments(self, mock_repo):
        """Test importing rules with assignments."""
        importer = BatchRuleImporter(mock_repo)
        
        csv_content = """rule_name,rule_type,rule_category,severity_level,rule_logic,created_by,target_source,target_schema,target_table,target_columns,execution_frequency
Email Check,single_field,accuracy,high,is_email(col('email')),admin,Test S3 Source,public,users,email,batch"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            result = importer.import_from_csv(temp_path, create_assignments=True)
            assert result["rules_created"] == 1
            assert result["assignments_created"] == 1
            mock_repo.create_rule.assert_called_once()
            mock_repo.assign_rule.assert_called_once()
        finally:
            os.unlink(temp_path)

    def test_import_invalid_source(self, mock_repo):
        """Test importing with invalid data source."""
        importer = BatchRuleImporter(mock_repo)
        mock_repo.list_data_sources.return_value = []  # No sources
        
        csv_content = """rule_name,rule_type,rule_category,severity_level,rule_logic,created_by,target_source,target_schema,target_table,target_columns,execution_frequency
Email Check,single_field,accuracy,high,is_email(col('email')),admin,NonExistent Source,public,users,email,batch"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            result = importer.import_from_csv(temp_path, create_assignments=True)
            assert result["rules_created"] == 1
            assert result["errors"] == 1  # Assignment failed
        finally:
            os.unlink(temp_path)
