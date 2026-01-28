#!/bin/bash
# Deployment script for Rules Engine Framework

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed. Please install Terraform first."
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials are not configured. Please run 'aws configure' first."
    exit 1
fi

# Parse command line arguments
ACTION=${1:-plan}

case $ACTION in
    init)
        print_info "Initializing Terraform..."
        terraform init
        ;;
    plan)
        print_info "Running Terraform plan..."
        terraform plan -out=tfplan
        ;;
    apply)
        print_info "Applying Terraform configuration..."
        if [ -f "tfplan" ]; then
            terraform apply tfplan
        else
            terraform apply
        fi
        ;;
    destroy)
        print_warn "This will destroy all resources. Are you sure? (yes/no)"
        read -r response
        if [ "$response" = "yes" ]; then
            terraform destroy
        else
            print_info "Destroy cancelled."
        fi
        ;;
    output)
        print_info "Showing Terraform outputs..."
        terraform output
        ;;
    validate)
        print_info "Validating Terraform configuration..."
        terraform validate
        ;;
    fmt)
        print_info "Formatting Terraform files..."
        terraform fmt -recursive
        ;;
    *)
        echo "Usage: $0 {init|plan|apply|destroy|output|validate|fmt}"
        echo ""
        echo "Commands:"
        echo "  init     - Initialize Terraform"
        echo "  plan     - Create execution plan"
        echo "  apply    - Apply the configuration"
        echo "  destroy  - Destroy all resources"
        echo "  output   - Show outputs"
        echo "  validate - Validate configuration"
        echo "  fmt      - Format Terraform files"
        exit 1
        ;;
esac

print_info "Done!"
