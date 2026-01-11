# Testing

Guidelines for writing and running tests.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=swb --cov-report=html

# Run specific file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_client_initialization

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Test Structure

Tests are organized by module:

```
tests/
├── test_api.py          # API client tests
├── test_cli.py          # CLI tests
├── test_models.py       # Data model tests
└── test_profiles.py     # Profile system tests
```

## Writing Tests

### Basic Test

```python
def test_search_basic(client: SWBClient) -> None:
    """Test basic search functionality."""
    response = client.search("Python", maximum_records=5)
    assert response.total_results > 0
    assert len(response.results) <= 5
```

### Using Fixtures

```python
@pytest.fixture
def client() -> SWBClient:
    """Create SWBClient instance."""
    return SWBClient()

def test_with_fixture(client: SWBClient) -> None:
    """Test using fixture."""
    response = client.search("Python")
    assert response.total_results > 0
```

### Mocking API Calls

```python
from unittest.mock import Mock, patch

def test_with_mock():
    """Test with mocked API call."""
    with patch('requests.Session.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<xml>...</xml>'
        mock_get.return_value = mock_response

        client = SWBClient()
        response = client.search("Python")
        # Test with mocked response
```

## Coverage

View coverage report:

```bash
pytest --cov=swb --cov-report=html
open htmlcov/index.html
```

Current coverage: **63%**

## Next Steps

- [Code Quality](code-quality.md) - Linting and formatting
- [Contributing](contributing.md) - Contribution guidelines
