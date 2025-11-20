#!/bin/bash
# Purpose: Run all test suites and generate test report
# Created/Updated: 2025-11-20
# Agent: QA_AGENT

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "=========================================="
echo "Running Automation Hub Test Suite"
echo "=========================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest is not installed"
    echo "Install with: pip install pytest pytest-cov"
    exit 1
fi

# Run tests with coverage
echo "Running tests with coverage..."
pytest tests/ \
    -v \
    --tb=short \
    --cov=shared \
    --cov=ops \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    -p no:warnings \
    "$@"

TEST_EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed"
    echo "Coverage report: htmlcov/index.html"
else
    echo "❌ Some tests failed"
fi
echo "=========================================="

exit $TEST_EXIT_CODE

