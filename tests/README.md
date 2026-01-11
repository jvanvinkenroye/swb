# SWB API Client Tests

This directory contains the test suite for the SWB API Client.

## Test Structure

### Unit Tests
- `test_api.py` - Core API functionality tests (43 tests)
- `test_api_validation.py` - Input validation tests (27 tests)
- `test_edge_cases.py` - Edge cases and error scenarios (22 tests)
- `test_cli.py` - CLI interface tests (22 tests)
- `test_models.py` - Data model tests (6 tests)
- `test_profiles.py` - Library profile tests (14 tests)

### Integration Tests
- `test_integration.py` - Real API call tests (19 tests, requires network)

## Running Tests

### Run all unit tests (fast, no network required)
```bash
pytest -m "not integration"
```

### Run all tests including integration tests
```bash
pytest
```

### Run only integration tests
```bash
pytest -m integration
```

### Run without slow tests
```bash
pytest -m "not slow"
```

### Run specific test file
```bash
pytest tests/test_edge_cases.py
```

### Run with verbose output
```bash
pytest -v
```

### Run with coverage report
```bash
pytest --cov=swb --cov-report=term-missing
```

## Test Coverage

Current coverage (as of latest run):
- **Overall: 64%**
- api.py: 94%
- models.py: 100%
- profiles.py: 100%
- cli.py: 52% (CLI interaction harder to test)
- tui.py: 3% (UI testing not automated)

## Test Markers

Tests are marked with the following pytest markers:

- `@pytest.mark.integration` - Tests that make real API calls (requires network)
- `@pytest.mark.slow` - Tests that take longer to run (>1 second)

These markers can be used to selectively run or skip tests:

```bash
# Skip integration tests (fast, no network)
pytest -m "not integration"

# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Skip both integration and slow tests
pytest -m "not integration and not slow"
```

## Test Categories

### Edge Case Tests (`test_edge_cases.py`)

Tests for uncommon scenarios and error conditions:

1. **Network Errors**
   - Connection timeout
   - Connection errors
   - Read timeout

2. **HTTP Errors**
   - 500 Internal Server Error
   - 502 Bad Gateway
   - 503 Service Unavailable
   - 403 Forbidden (with helpful error message)

3. **Malformed XML**
   - Completely invalid XML
   - Incomplete/truncated XML
   - Wrong XML structure

4. **Empty Responses**
   - Empty response body
   - Whitespace-only responses

5. **search_related() Edge Cases**
   - All relation types (CHILD, PARENT, FAMILY)
   - Network errors

6. **Character Encoding**
   - UTF-8 with umlauts (äöü)
   - Special characters

7. **Context Manager**
   - Session cleanup
   - Exception handling

8. **Rate Limiting**
   - Warning for large maximum_records

9. **Faceted Search**
   - Facet parameters

### Integration Tests (`test_integration.py`)

Tests that make actual API calls to the SWB/K10plus servers:

1. **Search Operations**
   - Basic queries
   - ISBN search
   - Title/Author/Subject indices
   - Different record formats (MARCXML, TurboMARC)

2. **Scan Operations**
   - Title index scanning
   - Author index scanning

3. **Explain Operations**
   - Server information retrieval
   - Available indices

4. **Holdings**
   - Holdings information availability

5. **Different Profiles**
   - K10plus endpoint
   - DNB endpoint (skipped due to access requirements)

6. **Performance**
   - Response time checks
   - Connection reuse

7. **Error Handling**
   - Unusual queries
   - Very long queries

## Writing New Tests

### Unit Test Example
```python
def test_my_feature(client: SWBClient) -> None:
    """Test my new feature."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """<xml>...</xml>"""
        mock_get.return_value = mock_response

        result = client.my_feature()
        assert result is not None
```

### Integration Test Example
```python
@pytest.mark.integration
def test_real_api_feature() -> None:
    """Test feature with real API."""
    with SWBClient() as client:
        response = client.my_feature()
        assert response is not None
```

## CI/CD Integration

The test suite is designed to work with continuous integration:

```yaml
# Run fast unit tests in CI
- run: pytest -m "not integration and not slow"

# Run all tests including integration (optional)
- run: pytest
```

## Troubleshooting

### Integration Tests Failing

If integration tests fail, it may be due to:
1. No network connection
2. SRU server temporarily unavailable
3. Rate limiting from the server
4. Changed API responses

Solution: Run without integration tests:
```bash
pytest -m "not integration"
```

### Slow Test Execution

If tests are running slow:
1. Run without slow tests: `pytest -m "not slow"`
2. Run specific test file instead of full suite
3. Use pytest-xdist for parallel execution: `pytest -n auto`

### Coverage Too Low

To see what's not covered:
```bash
pytest --cov=swb --cov-report=html
open htmlcov/index.html
```

## Best Practices

1. **Keep tests fast** - Mock external API calls in unit tests
2. **Use fixtures** - Reuse common test setup with pytest fixtures
3. **Test edge cases** - Don't just test the happy path
4. **Clear test names** - Test name should describe what's being tested
5. **One assertion per test** - Makes failures easier to debug
6. **Mark appropriately** - Use `@pytest.mark.integration` for network tests
7. **Document complex tests** - Add docstrings explaining what's being tested
