"""Batch rule import utility for CSV/Excel files."""

import csv
from typing import Any, Dict, List, Optional

import pandas as pd

from src.metadata.models import RuleAssignment, RuleCategory, RuleType, SeverityLevel
from src.metadata.repository import MetadataRepository
from src.utils.exceptions import MetadataException
from src.utils.logger import get_logger


class BatchRuleImporter:
    """Utility for importing rules and assignments from CSV/Excel files."""

    def __init__(self, metadata_repository: MetadataRepository):
        """
        Initialize batch importer.

        Args:
            metadata_repository: Metadata repository instance
        """
        self.repo = metadata_repository
        self.logger = get_logger(self.__class__.__name__)

    def import_from_csv(
        self,
        file_path: str,
        create_assignments: bool = True,
    ) -> Dict[str, Any]:
        """
        Import rules and assignments from CSV file.

        Expected CSV columns:
        - rule_name, rule_type, rule_category, severity_level, rule_logic
        - threshold_value (optional), description (optional), created_by
        - target_source (for assignment), target_schema, target_table, target_columns
        - execution_frequency (for assignment), schedule_expression (optional)

        Args:
            file_path: Path to CSV file
            create_assignments: Whether to create assignments automatically

        Returns:
            Dictionary with import summary
        """
        try:
            df = pd.read_csv(file_path)
            return self._import_from_dataframe(df, create_assignments)
        except Exception as e:
            raise MetadataException(f"Failed to import from CSV: {str(e)}") from e

    def import_from_excel(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        create_assignments: bool = True,
    ) -> Dict[str, Any]:
        """
        Import rules and assignments from Excel file.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name (uses first sheet if not specified)
            create_assignments: Whether to create assignments automatically

        Returns:
            Dictionary with import summary
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            return self._import_from_dataframe(df, create_assignments)
        except Exception as e:
            raise MetadataException(f"Failed to import from Excel: {str(e)}") from e

    def _import_from_dataframe(
        self,
        df: pd.DataFrame,
        create_assignments: bool = True,
    ) -> Dict[str, Any]:
        """
        Import rules and assignments from pandas DataFrame.

        Args:
            df: DataFrame with rule/assignment data
            create_assignments: Whether to create assignments

        Returns:
            Import summary dictionary
        """
        required_columns = [
            "rule_name",
            "rule_type",
            "rule_category",
            "severity_level",
            "rule_logic",
            "created_by",
        ]

        # Validate required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise MetadataException(
                f"Missing required columns: {', '.join(missing_columns)}"
            )

        rules_created = []
        assignments_created = []
        errors = []

        for idx, row in df.iterrows():
            try:
                # Create rule
                rule = ValidationRule(
                    rule_name=str(row["rule_name"]),
                    rule_type=RuleType(row["rule_type"]),
                    rule_category=RuleCategory(row["rule_category"]),
                    severity_level=SeverityLevel(row["severity_level"]),
                    rule_logic=str(row["rule_logic"]),
                    threshold_value=float(row["threshold_value"])
                    if pd.notna(row.get("threshold_value"))
                    else None,
                    description=str(row["description"])
                    if pd.notna(row.get("description"))
                    else None,
                    created_by=str(row["created_by"]),
                )

                rule_id = self.repo.create_rule(rule)
                rules_created.append({"rule_id": str(rule_id), "rule_name": rule.rule_name})

                # Create assignment if requested and columns provided
                if create_assignments and all(
                    col in df.columns
                    for col in [
                        "target_source",
                        "target_schema",
                        "target_table",
                        "target_columns",
                        "execution_frequency",
                    ]
                ):
                    # Get source ID by name
                    sources = self.repo.list_data_sources()
                    source = next(
                        (s for s in sources if s.source_name == row["target_source"]), None
                    )
                    if not source:
                        errors.append(
                            {
                                "row": idx + 1,
                                "error": f"Data source not found: {row['target_source']}",
                            }
                        )
                        continue

                    # Parse column names (comma-separated string or list)
                    column_names = (
                        row["target_columns"].split(",")
                        if isinstance(row["target_columns"], str)
                        else row["target_columns"]
                    )
                    column_names = [col.strip() for col in column_names]

                    assignment = RuleAssignment(
                        rule_id=rule_id,
                        source_id=source.source_id,
                        schema_name=str(row["target_schema"]),
                        table_name=str(row["target_table"]),
                        column_names=column_names,
                        execution_frequency=row["execution_frequency"],
                        schedule_expression=str(row["schedule_expression"])
                        if pd.notna(row.get("schedule_expression"))
                        else None,
                        created_by=str(row["created_by"]),
                    )

                    assignment_id = self.repo.assign_rule(assignment)
                    assignments_created.append(
                        {
                            "assignment_id": str(assignment_id),
                            "rule_name": rule.rule_name,
                            "table": f"{row['target_schema']}.{row['target_table']}",
                        }
                    )

            except Exception as e:
                errors.append({"row": idx + 1, "error": str(e)})
                self.logger.error("Failed to import row", row=idx + 1, error=str(e))

        return {
            "total_rows": len(df),
            "rules_created": len(rules_created),
            "assignments_created": len(assignments_created),
            "errors": len(errors),
            "rules": rules_created,
            "assignments": assignments_created,
            "error_details": errors,
        }

    def validate_import_file(self, file_path: str, file_type: str = "csv") -> Dict[str, Any]:
        """
        Validate import file before importing.

        Args:
            file_path: Path to import file
            file_type: File type ('csv' or 'excel')

        Returns:
            Validation results dictionary
        """
        try:
            if file_type == "csv":
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            required_columns = [
                "rule_name",
                "rule_type",
                "rule_category",
                "severity_level",
                "rule_logic",
                "created_by",
            ]

            missing_columns = [col for col in required_columns if col not in df.columns]
            empty_rows = df[df["rule_name"].isna()].index.tolist()

            return {
                "valid": len(missing_columns) == 0 and len(empty_rows) == 0,
                "total_rows": len(df),
                "missing_columns": missing_columns,
                "empty_rows": empty_rows,
                "columns": list(df.columns),
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
