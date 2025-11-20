# Development Setup Guide

## Virtual Environment Setup

This project uses a Python virtual environment to manage dependencies.

### Initial Setup

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   ```

2. **Activate virtual environment:**
   ```bash
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements-dev.txt
   ```

### Dependencies

- **Production dependencies** (`requirements.txt`):
  - `PyYAML` - YAML parsing for configuration and state files

- **Development dependencies** (`requirements-dev.txt`):
  - `pytest` - Testing framework
  - `pytest-cov` - Test coverage reporting
  - `jsonschema` - JSON schema validation
  - `greenlet` - Lightweight coroutines (development utility)
  - `setuptools`, `wheel` - Build tools

### Running Tests

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=shared --cov=ops --cov-report=html

# Or use the test runner script
./tests/run_all_tests.sh
```

### Virtual Environment Location

The virtual environment is located at:
```
pratejra-automation-hub/venv/
```

This directory is excluded from version control (see `.gitignore`).

### Updating Dependencies

To update dependencies:

1. Activate virtual environment
2. Install/update packages:
   ```bash
   pip install --upgrade package-name
   ```
3. Update requirements files:
   ```bash
   pip freeze > requirements-freeze.txt  # For reference
   ```

### Troubleshooting

**Virtual environment not activating:**
- Ensure you're using Python 3.11 or higher
- Check that `venv/bin/activate` exists
- Try recreating: `rm -rf venv && python3 -m venv venv`

**Dependencies not installing:**
- Upgrade pip: `pip install --upgrade pip`
- Check Python version: `python --version` (should be 3.11+)

