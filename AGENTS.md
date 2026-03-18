# AGENTS.md

This document provides guidelines and commands for agentic coding assistants working on this IPND reconciliation project.

## Development Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install recommended development tools
pip install pytest pytest-cov black flake8 mypy
```

## Running the Project

```bash
# Run main script
python3 main.py
```

## Testing

```bash
# Run all tests
pytest

# Run single test file
pytest tests/test_module.py

# Run single test function
pytest tests/test_module.py::test_function_name

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run tests with verbose output
pytest -v
```

## Linting and Formatting

```bash
# Format code with Black
black .

# Check Black formatting without changing files
black --check .

# Lint with flake8
flake8 .

# Auto-fix flake8 issues where possible (requires pyproject.cfg with autoflake)
autoflake --in-place --remove-unused-variables --remove-all-unused-imports .

# Type check with mypy
mypy .

# Full quality check pipeline
black --check . && flake8 . && mypy . && pytest
```

## Code Style Guidelines

### Imports
- Standard library imports first (e.g., `import re`, `from datetime import datetime`)
- Third-party imports second (e.g., `import pandas as pd`)
- Local imports third
- Each import type separated by blank line
- Use aliases for frequently used modules (e.g., `import pandas as pd`)

### Formatting
- Use 4 spaces for indentation (no tabs)
- Use Black formatter for consistent style
- Maximum line length: 88 characters (Black default)
- Use spaces around operators: `x == y` not `x==y`
- Use spaces after commas in function calls: `func(a, b)` not `func(a,b)`

### Types
- Add type hints to function signatures and variables
- Use Optional[T] for nullable types
- Type hints are mandatory for public functions and complex logic
- Example: `def process_data(data: pd.DataFrame) -> Optional[pd.DataFrame]:`

### Naming Conventions
- Variables and functions: `snake_case` (e.g., `active_service_report`)
- Classes: `PascalCase` (e.g., `DataProcessor`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- Private methods: `_snake_case` (e.g., `_validate_input`)
- Descriptive names preferred over abbreviations (e.g., `disconnection_report` not `discon_rpt`)

### Error Handling
- Always use `try-except` blocks around I/O operations
- Log errors with context: `logger.error(f"Failed to load {file}: {e}")`
- Raise custom exceptions for domain-specific errors
- Handle specific exceptions rather than broad `except:`
- Use context managers for resource management: `with pd.ExcelWriter(...)` or `open(...)`

### Code Organization
- Use functions for reusable logic rather than inline code
- Use docstrings to explain function purpose and parameters
- Keep functions under 50 lines when possible
- Break complex logic into smaller helper functions
- Store constants at module level (e.g., regex patterns)
- Boolean conditions: use parentheses for multi-line conditions

### Pandas/Data Processing
- Use descriptive column names
- Use `inplace=False` for method chaining preference
- Prefer `assign()` and `pipe()` for transformations
- Use `with pd.ExcelWriter()` for file operations
- Always validate data frame schemas before processing
- Use `astype()` for explicit type conversion

### Documentation
- Add docstrings to all functions with purpose, parameters, and returns
- Use triple-quoted strings for multi-line comments
- Update README.md for feature changes
- Document data schemas in code comments

### Git Workflow
- Never commit CSV, Excel, or generated files (tracked in .gitignore)
- Never commit venv directory
- Write descriptive commit messages
- Branch: feature/description or bugfix/description