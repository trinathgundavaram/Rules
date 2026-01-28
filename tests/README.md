# Test Suite Documentation

## Overview

The test suite for Rules Engine Framework includes comprehensive unit tests, integration tests, and test fixtures.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── unit/                    # Unit tests
│   ├── test_connectors.py
│   ├── test_rules_parser.py
│   ├── test_rules_functions.py
│   ├── test_single_field_validator.py
│   ├── test_multi_field_validator.py
│   └── test_metadata_models.py
├── integration/             # Integration tests
│   └── test_end_to_end.py
├── fixtures/                # Test fixtures and sample data
│   └── sample_data.py
└── test_batch_import.py     # Batch import utility tests
```

## Running Tests

### Run All Tests

```bash
# Using pytest directly
pytest tests/ -v

# Using the test runner script
chmod +x run_tests.sh
./run_tests.sh
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v -m integration

# Tests with coverage
pytest tests/ --cov=src --cov-report=html

# Skip integration tests (if DB not available)
SKIP_INTEGRATION=true pytest tests/
```

### Run Individual Test Files

```bash
# Test metadata models
pytest tests/unit/test_metadata_models.py -v

# Test rule parser
pytest tests/unit/test_rules_parser.py -v

# Test validators
pytest tests/unit/test_single_field_validator.py -v
```

## Test Coverage

### Unit Tests

1. **Connectors** (`test_connectors.py`)
   - ConnectorFactory creation
   - S3 connector initialization
   - Context manager usage
   - Filter and column selection

2. **Rule Parser** (`test_rules_parser.py`)
   - Column reference parsing
   - Function call parsing
   - SQL-style expression parsing
   - Column mapping
   - Invalid expression handling

3. **Rule Functions** (`test_rules_functions.py`)
   - is_null/is_not_null
   - is_empty/is_not_empty
   - is_email
   - range_check
   - length_check
   - is_in_list
   - equals/greater_than/less_than
   - Function registry

4. **Single-Field Validator** (`test_single_field_validator.py`)
   - Completeness validation
   - Accuracy validation (email, range)
   - Rule-based validation
   - Threshold handling
   - Invalid rule logic handling

5. **Multi-Field Validator** (`test_multi_field_validator.py`)
   - Consistency validation (equals, greater_than)
   - Business logic validation
   - Multi-column rule execution

6. **Metadata Models** (`test_metadata_models.py`)
   - DataSource model validation
   - ValidationRule model validation
   - RuleAssignment model validation
   - ValidationResult calculations
   - ExecutionLog duration calculation
   - QualityScore validation

### Integration Tests

1. **End-to-End Workflow** (`test_end_to_end.py`)
   - Complete validation workflow
   - Batch execution
   - Mock connector integration
   - Repository interaction

### Utility Tests

1. **Batch Import** (`test_batch_import.py`)
   - CSV file validation
   - Rule import from CSV
   - Assignment creation
   - Error handling

## Test Fixtures

### Available Fixtures (in `conftest.py`)

- `spark_session`: Spark session for testing
- `mock_metadata_repo`: Mock metadata repository
- `sample_data_source`: Sample DataSource model
- `sample_rule`: Sample ValidationRule model
- `sample_assignment`: Sample RuleAssignment model
- `sample_spark_dataframe`: Sample DataFrame with test data
- `mock_connector`: Mock connector instance

### Usage Example

```python
def test_my_function(sample_spark_dataframe, mock_metadata_repo):
    # Use fixtures in your tests
    df = sample_spark_dataframe
    repo = mock_metadata_repo
    # ... your test code
```

## Test Markers

Tests are marked with pytest markers:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Slow-running tests
- `@pytest.mark.requires_db`: Tests requiring database
- `@pytest.mark.requires_spark`: Tests requiring Spark

Run tests by marker:

```bash
pytest -m unit          # Run only unit tests
pytest -m integration  # Run only integration tests
pytest -m "not slow"   # Skip slow tests
```

## Mocking

Tests use `unittest.mock` for mocking external dependencies:

- Database connections
- AWS services (S3, Glue, Lambda)
- Spark sessions (where appropriate)
- Connector implementations

## Sample Data

Test fixtures include sample data in `tests/fixtures/sample_data.py`:

- Sample CSV for batch import
- Sample rule definitions
- Sample connection configurations

## Continuous Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ --cov=src --cov-report=xml
```

## Coverage Goals

- Target coverage: 70%+ (configured in `pytest.ini`)
- Current focus: Core components (connectors, rules engine, repository)
- Future: Expand to Lambda functions and Glue jobs

## Troubleshooting

### Tests Failing Due to Missing Dependencies

```bash
pip install -r requirements.txt
```

### Spark Session Issues

Ensure PySpark is installed:
```bash
pip install pyspark
```

### Database Connection Issues

Integration tests require a database. Skip them if not available:
```bash
SKIP_INTEGRATION=true pytest tests/
```

Or mock the database connection in your tests.

## Writing New Tests

1. Follow existing test patterns
2. Use fixtures from `conftest.py`
3. Mock external dependencies
4. Add appropriate markers
5. Include docstrings explaining what is tested
6. Aim for >80% coverage of new code

## Test Examples

See individual test files for examples of:
- Testing Pydantic models
- Testing Spark DataFrame operations
- Testing rule parsing and execution
- Mocking AWS services
- Testing error handling
