#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}

if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <environment>"
    echo "Example: $0 dev"
    exit 1
fi

echo "Deploying to $ENVIRONMENT environment..."

# Build Lambda packages
echo "Building Lambda packages..."
./scripts/build_lambdas.sh

# Build UI
echo "Building UI..."
cd src/ui/frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run build
cd ../../..

# Deploy infrastructure
echo "Deploying infrastructure..."
cd terragrunt/envs/$ENVIRONMENT
terragrunt apply -auto-approve
cd ../../..

# Run database migrations
echo "Running database migrations..."
./scripts/run_migrations.sh $ENVIRONMENT

# Upload UI to S3
echo "Uploading UI to S3..."
UI_BUCKET=$(cd terragrunt/envs/$ENVIRONMENT && terragrunt output -raw ui_bucket_name 2>/dev/null || echo "")
if [ -n "$UI_BUCKET" ]; then
    aws s3 sync src/ui/frontend/build/ "s3://$UI_BUCKET/" --delete
    echo "UI uploaded to s3://$UI_BUCKET"
    
    # Create CloudFront invalidation
    CF_ID=$(cd terragrunt/envs/$ENVIRONMENT && terragrunt output -raw cloudfront_distribution_id 2>/dev/null || echo "")
    if [ -n "$CF_ID" ]; then
        aws cloudfront create-invalidation \
            --distribution-id "$CF_ID" \
            --paths "/*" \
            --quiet
        echo "CloudFront cache invalidated"
    fi
else
    echo "Warning: UI bucket not found. Skipping UI deployment."
fi

echo ""
echo "Deployment complete!"
echo ""
echo "Get outputs:"
echo "  cd terragrunt/envs/$ENVIRONMENT"
echo "  terragrunt output"
