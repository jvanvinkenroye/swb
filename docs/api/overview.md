# API Overview

The SWB API Client provides a clean Python API for integrating library catalog searches into your applications.

## Quick Example

```python
from swb import SWBClient, SearchIndex

# Create client
with SWBClient() as client:
    # Simple search
    response = client.search(
        "Python programming",
        index=SearchIndex.TITLE,
        maximum_records=10
    )

    # Process results
    for result in response.results:
        print(f"{result.title} by {result.author} ({result.year})")
```

## Key Components

### SWBClient

The main client class for making API requests.

```python
from swb import SWBClient

# Default SWB endpoint
client = SWBClient()

# Custom endpoint
client = SWBClient(base_url="https://custom.sru.endpoint.de/sru")

# With timeout
client = SWBClient(timeout=60)
```

### Search Methods

- `search()` - General search with CQL queries
- `search_by_isbn()` - Search by ISBN
- `search_by_issn()` - Search by ISSN
- `search_related()` - Find related records
- `scan()` - Browse index terms
- `explain()` - Get server capabilities

### Response Objects

- `SearchResponse` - Contains search results and metadata
- `SearchResult` - Individual catalog record
- `ScanResponse` - Index browsing results
- `ExplainResponse` - Server capabilities

### Data Models

- `SearchIndex` - Available search indices
- `RecordFormat` - Output format options
- `SortBy`, `SortOrder` - Sorting options
- `RelationType` - For related records
- `RecordType` - Bibliographic or authority records

## Basic Usage Patterns

### Context Manager (Recommended)

```python
from swb import SWBClient

with SWBClient() as client:
    response = client.search("query")
    # Client automatically closed
```

### Manual Session Management

```python
from swb import SWBClient

client = SWBClient()
try:
    response = client.search("query")
finally:
    client.close()
```

### Using Profiles

```python
from swb import SWBClient
from swb.profiles import get_profile

# Get profile
profile = get_profile("k10plus")

# Use profile URL
with SWBClient(base_url=profile.url) as client:
    response = client.search("query")
```

## Common Operations

### Searching

```python
from swb import SWBClient, SearchIndex, RecordFormat

with SWBClient() as client:
    response = client.search(
        query="Python",
        index=SearchIndex.TITLE,
        record_format=RecordFormat.MARCXML,
        maximum_records=20,
        start_record=1
    )
```

### ISBN Lookup

```python
with SWBClient() as client:
    response = client.search_by_isbn("978-3-16-148410-0")

    if response.results:
        book = response.results[0]
        print(f"Found: {book.title}")

        # Check holdings
        for holding in book.holdings:
            print(f"Available at: {holding.library_name}")
```

### Sorting Results

```python
from swb import SWBClient, SortBy, SortOrder

with SWBClient() as client:
    response = client.search(
        "Machine Learning",
        sort_by=SortBy.YEAR,
        sort_order=SortOrder.DESCENDING
    )
```

### Index Scanning

```python
with SWBClient() as client:
    scan_response = client.scan(
        scan_clause="pica.per=Goe",
        maximum_terms=10
    )

    for term in scan_response.terms:
        print(f"{term.value}: {term.number_of_records} records")
```

## Error Handling

```python
from swb import SWBClient
import requests

with SWBClient() as client:
    try:
        response = client.search("query")
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            print("Access denied - try different profile")
        else:
            print(f"HTTP error: {e}")
    except ValueError as e:
        print(f"Invalid query: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Type Safety

The API is fully typed and works with mypy:

```python
from swb import SWBClient, SearchResponse, SearchResult

def process_results(response: SearchResponse) -> list[str]:
    """Extract titles from response."""
    return [
        result.title
        for result in response.results
        if result.title is not None
    ]

with SWBClient() as client:
    response: SearchResponse = client.search("Python")
    titles: list[str] = process_results(response)
```

## Next Steps

- [SWBClient Reference](client.md) - Detailed client documentation
- [Models Reference](models.md) - All data models
- [Profiles API](profiles.md) - Working with catalog profiles
