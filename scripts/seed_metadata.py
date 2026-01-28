#!/usr/bin/env python3
"""
Seed metadata database with sample data.
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import boto3
import json

from metadata.models import Base, DataSource, ValidationRule, RuleAssignment


def get_db_connection(env: str):
    """Get database connection from config or Secrets Manager."""
    config_path = Path(__file__).parent.parent / "config" / f"{env}.yaml"
    
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
            db_config = config.get("database", {})
            
            host = db_config.get("host")
            port = db_config.get("port", 5432)
            name = db_config.get("name")
            username = db_config.get("username")
            password = db_config.get("password")
            
            if all([host, name, username, password]):
                return f"postgresql://{username}:{password}@{host}:{port}/{name}"
    
    # Try to get from Terraform output
    print("Attempting to get database credentials from Secrets Manager...")
    # This would require terraform output parsing - simplified for now
    print("Please ensure database credentials are in config/{env}.yaml")
    sys.exit(1)


def seed_sample_data(session):
    """Seed database with sample data."""
    
    # Sample data source
    source = DataSource(
        source_name="Sample SQL Server",
        source_type="sqlserver",
        connection_config={
            "host": "sample-server.database.windows.net",
            "port": 1433,
            "database": "sample_db"
        },
        is_active=True
    )
    session.add(source)
    session.flush()
    
    # Sample rules
    rules = [
        ValidationRule(
            rule_name="Email Format Validation",
            rule_type="single_field",
            rule_category="accuracy",
            severity_level="high",
            rule_logic="column RLIKE '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'",
            is_reusable=True,
            created_by="system"
        ),
        ValidationRule(
            rule_name="Not Null Check",
            rule_type="single_field",
            rule_category="completeness",
            severity_level="critical",
            rule_logic="column IS NOT NULL",
            is_reusable=True,
            created_by="system"
        ),
        ValidationRule(
            rule_name="Age Range Check",
            rule_type="single_field",
            rule_category="accuracy",
            severity_level="medium",
            rule_logic="column BETWEEN 0 AND 120",
            is_reusable=True,
            created_by="system"
        ),
    ]
    
    for rule in rules:
        session.add(rule)
    
    session.flush()
    
    # Sample assignment
    assignment = RuleAssignment(
        rule_id=rules[0].rule_id,
        source_id=source.source_id,
        schema_name="dbo",
        table_name="users",
        column_names=["email"],
        execution_frequency="daily",
        is_active=True,
        priority_order=1
    )
    session.add(assignment)
    
    session.commit()
    print("Sample data seeded successfully!")
    print(f"  - Created 1 data source")
    print(f"  - Created {len(rules)} validation rules")
    print(f"  - Created 1 rule assignment")


def main():
    parser = argparse.ArgumentParser(description="Seed metadata database")
    parser.add_argument("--env", default="dev", help="Environment name")
    parser.add_argument("--reset", action="store_true", help="Reset database before seeding")
    
    args = parser.parse_args()
    
    # Get database connection
    db_url = get_db_connection(args.env)
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        if args.reset:
            print("Resetting database...")
            Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)
        
        seed_sample_data(session)
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
