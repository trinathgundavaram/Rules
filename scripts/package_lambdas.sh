#!/bin/bash
# Package Lambda functions for deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LAMBDA_PACKAGES_DIR="$PROJECT_ROOT/module/aws/rules-engine/lambda_packages"

# Create packages directory
mkdir -p "$LAMBDA_PACKAGES_DIR"

echo "Packaging Lambda functions..."

# Function to package a Lambda
package_lambda() {
    local lambda_name=$1
    local lambda_dir="$PROJECT_ROOT/src/lambda/$lambda_name"
    local temp_dir=$(mktemp -d)
    
    echo "Packaging $lambda_name..."
    
    # Copy source code
    cp -r "$lambda_dir"/* "$temp_dir/" 2>/dev/null || true
    
    # Install dependencies if requirements.txt exists
    if [ -f "$lambda_dir/requirements.txt" ]; then
        echo "  Installing dependencies..."
        pip install -r "$lambda_dir/requirements.txt" -t "$temp_dir/" --quiet --no-warn-script-location
    fi
    
    # Copy shared modules
    for module in connectors rules metadata utils; do
        if [ -d "$PROJECT_ROOT/src/$module" ]; then
            cp -r "$PROJECT_ROOT/src/$module" "$temp_dir/" 2>/dev/null || true
        fi
    done
    
    # Create ZIP
    cd "$temp_dir"
    zip -r "$LAMBDA_PACKAGES_DIR/$lambda_name.zip" . -q \
        -x "*.pyc" -x "__pycache__/*" -x "*.pytest_cache/*" -x ".pytest_cache/*" \
        -x "*.git*" -x "*.md" -x "*.txt" -x "tests/*"
    cd "$PROJECT_ROOT"
    
    # Cleanup
    rm -rf "$temp_dir"
    
    echo "  ✓ Created: $LAMBDA_PACKAGES_DIR/$lambda_name.zip ($(du -h "$LAMBDA_PACKAGES_DIR/$lambda_name.zip" | cut -f1))"
}

# Package all Lambda functions
package_lambda "rule_executor"
package_lambda "api_gateway"

echo ""
echo "Packaging complete!"
echo "Packages created in: $LAMBDA_PACKAGES_DIR"
ls -lh "$LAMBDA_PACKAGES_DIR"
