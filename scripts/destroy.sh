#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}

if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <environment>"
    echo "Example: $0 dev"
    echo ""
    echo "WARNING: This will destroy all resources in the $ENVIRONMENT environment!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        exit 1
    fi
fi

echo "Destroying $ENVIRONMENT environment..."

cd terragrunt/envs/$ENVIRONMENT

# Show what will be destroyed
echo "Reviewing resources to be destroyed..."
terragrunt plan -destroy

# Confirm
read -p "Proceed with destruction? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 1
fi

# Destroy
terragrunt destroy

echo ""
echo "Destruction complete!"
echo ""
echo "Note: S3 buckets and DynamoDB tables may need manual cleanup."
