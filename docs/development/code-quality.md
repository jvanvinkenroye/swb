# Code Quality

Tools and practices for maintaining code quality.

## Formatting

### Ruff Format

```bash
# Format all code
ruff format .

# Check formatting without changes
ruff format --check .

# Format specific file
ruff format src/swb/api.py
```

## Linting

### Ruff Lint

```bash
# Lint all code
ruff check .

# Fix issues automatically
ruff check --fix .

# Check specific file
ruff check src/swb/api.py
```

## Type Checking

### Mypy

```bash
# Type check all code
mypy src/swb

# Type check specific file
mypy src/swb/api.py

# Strict mode
mypy --strict src/swb
```

## Pre-commit Hooks

Set up pre-commit hooks to automatically check code:

```bash
# Install pre-commit
uv pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## CI/CD

GitHub Actions automatically runs:

- Tests
- Linting
- Type checking
- Coverage reporting

## Next Steps

- [Testing](testing.md) - Writing tests
- [Contributing](contributing.md) - Contribution guidelines
