#!/bin/bash
# Package Lambda functions for deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LAMBDA_PACKAGES_DIR="$PROJECT_ROOT/terraform/lambda_packages"

# Create packages directory
mkdir -p "$LAMBDA_PACKAGES_DIR"

echo "Packaging Lambda functions..."

# Package rule executor
echo "Packaging rule_executor..."
cd "$PROJECT_ROOT/src/lambda/rule_executor"
zip -r "$LAMBDA_PACKAGES_DIR/rule_executor.zip" . \
  -x "*.pyc" -x "__pycache__/*" -x "*.pytest_cache/*" -x ".pytest_cache/*"

# Package API Gateway
echo "Packaging api_gateway..."
cd "$PROJECT_ROOT/src/lambda/api_gateway"
zip -r "$LAMBDA_PACKAGES_DIR/api_gateway.zip" . \
  -x "*.pyc" -x "__pycache__/*" -x "*.pytest_cache/*" -x ".pytest_cache/*"

# Copy shared dependencies (if using Lambda Layers)
# This is a placeholder - customize based on your needs
echo "Packaging complete!"
echo "Packages created in: $LAMBDA_PACKAGES_DIR"

ls -lh "$LAMBDA_PACKAGES_DIR"
