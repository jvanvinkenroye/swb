# Contributing

Thank you for considering contributing to the SWB API Client! This document provides guidelines for contributors.

## Getting Started

### 1. Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/swb.git
cd swb
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
uv venv --seed
source .venv/bin/activate

# Install with dev dependencies
uv pip install -e ".[dev]"

# Or sync dependencies
uv sync --dev
```

### 3. Create a Branch

```bash
git checkout -b feature/amazing-feature
# or
git checkout -b fix/bug-description
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=swb --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_client_initialization
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Fix linting issues
ruff check --fix .

# Type check
mypy src/swb
```

### Running the Application

```bash
# Test CLI
swb search "Python" --max 5

# Test TUI
swb-tui
```

## Code Guidelines

### Python Style

- Follow PEP 8
- Use type hints for all functions
- Maximum line length: 88 characters
- Use descriptive variable names

### Docstrings

Use Google-style docstrings:

```python
def search(self, query: str, maximum_records: int = 10) -> SearchResponse:
    """Search the catalog with a query.

    Args:
        query: Search query in CQL format
        maximum_records: Maximum number of records to return

    Returns:
        SearchResponse object containing results

    Raises:
        ValueError: If query is invalid
        HTTPError: If server returns an error
    """
    pass
```

### Testing

- Write tests for new features
- Maintain or improve code coverage
- Use pytest fixtures
- Mock external API calls

Example test:

```python
def test_search_basic(client: SWBClient) -> None:
    """Test basic search functionality."""
    response = client.search("Python", maximum_records=5)
    assert response.total_results > 0
    assert len(response.results) <= 5
```

## Making Changes

### Adding a Feature

1. Create an issue describing the feature
2. Discuss approach with maintainers
3. Implement feature with tests
4. Update documentation
5. Submit pull request

### Fixing a Bug

1. Create an issue describing the bug
2. Write failing test that reproduces bug
3. Fix the bug
4. Ensure test passes
5. Submit pull request

### Updating Documentation

1. Edit relevant `.md` files in `docs/`
2. Run `mkdocs serve` to preview
3. Submit pull request

## Pull Request Process

### Before Submitting

- [ ] Tests pass: `pytest`
- [ ] Linting passes: `ruff check .`
- [ ] Types check: `mypy src/swb`
- [ ] Documentation updated
- [ ] Changelog updated (if applicable)

### PR Description

Include:

- **What**: What does this PR do?
- **Why**: Why is this change needed?
- **How**: How does it work?
- **Testing**: How was it tested?
- **Breaking**: Any breaking changes?

Example:

```markdown
## What
Adds support for MADS record format

## Why
Users requested support for authority records in MADS format

## How
- Added MADS to RecordFormat enum
- Updated parser to handle MADS XML
- Added tests for MADS parsing

## Testing
- Added test_parse_mads_record
- Manually tested with real API

## Breaking Changes
None
```

### Review Process

1. Maintainer reviews code
2. Automated tests run
3. Feedback provided
4. You make requested changes
5. PR approved and merged

## Commit Messages

Follow conventional commits:

```
feat: add MADS record format support
fix: correct ISBN validation regex
docs: update installation guide
test: add tests for profile system
refactor: simplify error handling
```

## Areas to Contribute

### High Priority

- [ ] Additional record format parsers
- [ ] More library catalog profiles
- [ ] TUI enhancements
- [ ] Performance improvements

### Medium Priority

- [ ] Better error messages
- [ ] More examples
- [ ] Additional tests
- [ ] Documentation improvements

### Low Priority

- [ ] UI themes
- [ ] Additional output formats
- [ ] Shell completion improvements

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Features**: Open a GitHub Issue

## Code of Conduct

Be respectful and inclusive. We're all here to make this project better.

## Recognition

Contributors are listed in:
- GitHub contributors page
- Release notes
- CONTRIBUTORS.md file

Thank you for contributing! 🎉
