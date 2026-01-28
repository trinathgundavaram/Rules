#!/bin/bash
set -e

echo "Building Lambda packages..."

DIST_DIR="dist/lambda-packages"
mkdir -p "$DIST_DIR"

# Function to build a Lambda package
build_lambda() {
    local lambda_name=$1
    local lambda_dir="src/lambda/$lambda_name"
    
    if [ ! -d "$lambda_dir" ]; then
        echo "Warning: Lambda directory not found: $lambda_dir"
        return
    fi
    
    echo "Building $lambda_name..."
    
    # Create temp directory
    local temp_dir=$(mktemp -d)
    trap "rm -rf $temp_dir" EXIT
    
    # Copy source code
    cp -r "$lambda_dir"/* "$temp_dir/" 2>/dev/null || true
    
    # Install dependencies if requirements.txt exists
    if [ -f "$lambda_dir/requirements.txt" ]; then
        echo "  Installing dependencies..."
        pip install -r "$lambda_dir/requirements.txt" -t "$temp_dir/" --quiet
    fi
    
    # Copy shared modules
    if [ -d "src/connectors" ]; then
        cp -r src/connectors "$temp_dir/" 2>/dev/null || true
    fi
    if [ -d "src/rules" ]; then
        cp -r src/rules "$temp_dir/" 2>/dev/null || true
    fi
    if [ -d "src/metadata" ]; then
        cp -r src/metadata "$temp_dir/" 2>/dev/null || true
    fi
    if [ -d "src/utils" ]; then
        cp -r src/utils "$temp_dir/" 2>/dev/null || true
    fi
    
    # Create ZIP
    cd "$temp_dir"
    zip -r "$OLDPWD/$DIST_DIR/$lambda_name.zip" . -q
    cd "$OLDPWD"
    
    echo "  Packaged: $DIST_DIR/$lambda_name.zip ($(du -h "$DIST_DIR/$lambda_name.zip" | cut -f1))"
}

# Build all Lambda functions
build_lambda "rule_executor"
build_lambda "api_gateway"

# Upload to S3 if code bucket is configured
CODE_BUCKET=$(cd terragrunt/envs/dev 2>/dev/null && terragrunt output -raw code_bucket_name 2>/dev/null || echo "")

if [ -n "$CODE_BUCKET" ]; then
    echo ""
    echo "Uploading packages to S3..."
    aws s3 sync "$DIST_DIR/" "s3://$CODE_BUCKET/lambda-packages/" --quiet
    echo "Uploaded to s3://$CODE_BUCKET/lambda-packages/"
else
    echo ""
    echo "Code bucket not found. Packages are in $DIST_DIR/"
    echo "Upload manually or deploy infrastructure first."
fi

echo ""
echo "Lambda packages built successfully!"
