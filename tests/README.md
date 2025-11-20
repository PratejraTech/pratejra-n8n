# Automation Hub Test Suite

## Overview

This directory contains comprehensive tests for the n8n Automation Hub architecture, including schema validation, JS snippets, configurations, catalog generation, CI/CD workflows, and integration points.

## Test Structure

- `test_schemas.py` - JSON schema validation tests
- `test_js_snippets.py` - JavaScript snippet tests
- `test_configs.py` - Configuration file validation tests
- `test_catalog_generation.py` - Catalog generation script tests
- `test_ci_workflows.py` - CI/CD workflow validation tests
- `test_integrations.py` - Integration tests with mocked services
- `test_architecture.py` - Architecture compliance tests
- `test_workflow_structure.py` - Workflow structure and naming tests
- `conftest.py` - Pytest fixtures and configuration
- `mocks/` - Mock data and service responses

## Running Tests

### Run All Tests

```bash
# From repository root
pytest tests/

# Or use the test runner script
./tests/run_all_tests.sh
```

### Run Specific Test Suites

```bash
# Test schemas only
pytest tests/test_schemas.py -v

# Test JS snippets only
pytest tests/test_js_snippets.py -v

# Test configurations only
pytest tests/test_configs.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=shared --cov=ops --cov-report=html
```

## Test Requirements

Install test dependencies:

```bash
pip install pytest pytest-cov jsonschema pyyaml
```

## Mock Services

All external service calls are mocked:
- n8n API
- AWS Secrets Manager
- Prometheus Push Gateway
- Slack API
- GitHub Actions environment

## Test Coverage

Tests validate:
- ✅ All schemas are valid JSON Schema
- ✅ All JS snippets function correctly
- ✅ All configurations are valid
- ✅ Catalog generation works
- ✅ CI/CD workflows are valid
- ✅ Integration points work (mocked)
- ✅ Architecture compliance

## Integration with CI/CD

Tests are automatically run in GitHub Actions via `validate-workflows.yml`.

