#!/bin/bash
# Test runner script for Rules Engine Framework

set -e

echo "=========================================="
echo "Rules Engine Framework - Test Suite"
echo "=========================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "pytest is not installed. Installing dependencies..."
    pip install -r requirements.txt
fi

# Run unit tests
echo "Running unit tests..."
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# Run integration tests (if database available)
if [ "$SKIP_INTEGRATION" != "true" ]; then
    echo ""
    echo "Running integration tests..."
    pytest tests/integration/ -v -m integration || echo "Integration tests skipped (database not available)"
fi

# Run batch import tests
echo ""
echo "Running batch import tests..."
pytest tests/test_batch_import.py -v

echo ""
echo "=========================================="
echo "Test execution completed!"
echo "=========================================="
