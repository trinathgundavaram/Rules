#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}

if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <environment>"
    exit 1
fi

echo "Running database migrations for $ENVIRONMENT..."

# Get database endpoint from Terraform output
cd terragrunt/envs/$ENVIRONMENT

DB_ENDPOINT=$(terragrunt output -raw db_endpoint 2>/dev/null || echo "")
DB_SECRET_ARN=$(terragrunt output -raw db_secret_arn 2>/dev/null || echo "")

if [ -z "$DB_ENDPOINT" ]; then
    echo "Error: Could not get database endpoint from Terraform output"
    echo "Make sure infrastructure is deployed first."
    exit 1
fi

cd ../../..

# Get database credentials from Secrets Manager
if [ -n "$DB_SECRET_ARN" ]; then
    echo "Retrieving database credentials from Secrets Manager..."
    SECRET=$(aws secretsmanager get-secret-value \
        --secret-id "$DB_SECRET_ARN" \
        --query SecretString --output text)
    
    DB_USERNAME=$(echo "$SECRET" | jq -r .username)
    DB_PASSWORD=$(echo "$SECRET" | jq -r .password)
    DB_NAME=$(echo "$SECRET" | jq -r .dbname)
else
    # Fallback: use environment variables or config file
    echo "Warning: DB_SECRET_ARN not found. Using config file or environment variables."
    source config/$ENVIRONMENT.yaml 2>/dev/null || true
    DB_USERNAME=${database_username:-rulesadmin}
    DB_PASSWORD=${database_password:-}
    DB_NAME=${database_name:-rules_engine_$ENVIRONMENT}
fi

if [ -z "$DB_PASSWORD" ]; then
    echo "Error: Database password not found"
    exit 1
fi

# Set PGPASSWORD environment variable
export PGPASSWORD="$DB_PASSWORD"

# Run schema
echo "Running database schema..."
psql -h "$DB_ENDPOINT" \
     -U "$DB_USERNAME" \
     -d "$DB_NAME" \
     -f sql/metadata_schema.sql

echo "Migrations completed successfully!"
