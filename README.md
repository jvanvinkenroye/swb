# SWB API Client

A Python CLI client for querying the Südwestdeutscher Bibliotheksverbund (SWB) library catalog via the SRU (Search/Retrieve via URL) API.

## Features

- Search the SWB catalog using CQL queries or simple keywords
- Support for multiple search indices (title, author, ISBN, ISSN, etc.)
- Index scanning for auto-completion and browsing terms
- Sort results by relevance, year, author, or title
- Multiple output formats (MARCXML, MODS, PICA, Dublin Core)
- Rich terminal output with formatted tables
- Export search results to files
- Comprehensive error handling and logging
- Type-safe with full mypy support
- Well-tested with pytest

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/swb.git
cd swb

# Create virtual environment and install dependencies
uv venv --seed
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install the package
uv pip install -e .
```

## Usage

### Basic Search

Search for books by keyword:

```bash
swb search "Python programming"
```

Search in a specific index:

```bash
swb search "Goethe" --index author
swb search "Machine Learning" --index title --max 20
```

### ISBN/ISSN Search

Search by ISBN:

```bash
swb isbn 978-3-16-148410-0
```

Search by ISSN:

```bash
swb issn 0028-0836
```

### Advanced Options

#### Output Format

Choose different record formats:

```bash
swb search "Python" --format mods
swb search "Python" --format picaxml
```

Available formats:
- `marcxml` (default) - MARC 21 XML format
- `mods` - Metadata Object Description Schema
- `picaxml` - PICA XML format
- `dc` - Dublin Core
- `isbd` - International Standard Bibliographic Description

#### Sorting

Sort search results by different criteria:

```bash
# Sort by year (newest first)
swb search "Python" --sort-by year --sort-order descending

# Sort by year (oldest first)
swb search "Python" --sort-by year --sort-order ascending

# Sort by author
swb search "Python" --sort-by author

# Sort by title
swb search "Machine Learning" --sort-by title
```

Available sort options:
- `relevance` - Sort by relevance ranking
- `year` - Sort by publication year
- `author` - Sort by author name
- `title` - Sort by title

Sort order:
- `descending` (default) - Newest/Z-A
- `ascending` - Oldest/A-Z

#### Index Scanning (Browse and Auto-completion)

Scan an index to browse terms and find the exact form of names, subjects, or titles:

```bash
# Find authors starting with "Goe"
swb scan "pica.per=Goe" --max 10

# Find titles starting with "Python"
swb scan "pica.tit=Python"

# Browse subjects starting with "Machine Learning"
swb scan "pica.sub=Machine Learning" --max 20
```

The scan operation is useful for:
- **Auto-completion**: Find all terms starting with a prefix
- **Browse index**: Explore what terms exist in a specific index
- **Find exact form**: Determine the exact spelling and form of author names or subjects
- **Discovery**: See how many records exist for each term

Example output shows:
- The term value (e.g., "Goethe, Johann Wolfgang von")
- Number of records for that term (e.g., 28,531 records)
- Display form of the term (when available)

**Note**: The scan operation may be temporarily unavailable due to server maintenance. In this case, you'll receive a clear diagnostic error message.

#### Pagination

Control the number of results and pagination:

```bash
# Get 20 results
swb search "Python" --max 20

# Get results starting from position 11
swb search "Python" --start-record 11 --max 10
```

#### Save Results to File

Export search results:

```bash
swb search "Python" --output results.txt
swb search "Python" --output results.txt --raw  # Include raw XML
```

#### Verbosity Control

```bash
# Verbose output (DEBUG level)
swb --verbose search "Python"

# Quiet mode (errors only)
swb --quiet search "Python"
```

### CQL Queries

Use full CQL syntax for complex queries:

```bash
# Boolean operators
swb search 'pica.tit="Python" and pica.per="Guido"'

# Wildcards
swb search 'pica.tit="Pytho*"'

# Multiple conditions
swb search 'pica.tit="Machine Learning" and pica.ejr=2023'
```

### List Available Options

Show available record formats:

```bash
swb formats
```

Show available search indices:

```bash
swb indices
```

### Help

Get help for any command:

```bash
swb --help
swb search --help
swb isbn --help
swb scan --help
```

## Development

### Setup Development Environment

```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Or using uv directly
uv sync --dev
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=swb --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v
```

### Code Quality

The project uses ruff for linting and formatting, and mypy for type checking:

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Fix linting issues automatically
ruff check --fix .

# Type check
mypy src/swb
```

### Project Structure

```
swb/
├── src/
│   └── swb/
│       ├── __init__.py      # Package initialization
│       ├── api.py           # SRU API client
│       ├── cli.py           # CLI interface
│       └── models.py        # Data models
├── tests/
│   ├── __init__.py
│   ├── test_api.py          # API client tests
│   ├── test_cli.py          # CLI tests
│   └── test_models.py       # Model tests
├── docs/                    # Documentation
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── .gitignore
```

## API Documentation

### SWBClient

The main API client class:

```python
from swb import SWBClient, SearchIndex, RecordFormat, SortBy, SortOrder

# Create client
with SWBClient() as client:
    # Simple search
    response = client.search(
        "Python programming",
        index=SearchIndex.TITLE,
        record_format=RecordFormat.MARCXML,
        maximum_records=10
    )

    # Search with sorting
    response = client.search(
        "Machine Learning",
        index=SearchIndex.TITLE,
        sort_by=SortBy.YEAR,
        sort_order=SortOrder.DESCENDING,
        maximum_records=20
    )

    # Search by ISBN
    response = client.search_by_isbn("978-3-16-148410-0")

    # Search by ISSN
    response = client.search_by_issn("0028-0836")

    # Scan index for terms (auto-completion)
    scan_response = client.scan(
        scan_clause="pica.per=Goe",
        maximum_terms=10,
        response_position=1
    )

    # Process results
    for result in response.results:
        print(f"Title: {result.title}")
        print(f"Author: {result.author}")
        print(f"Year: {result.year}")

    # Process scan results
    for term in scan_response.terms:
        print(f"{term.value}: {term.number_of_records} records")
```

### Search Response

The `SearchResponse` object contains:

- `total_results` - Total number of matching records
- `results` - List of `SearchResult` objects
- `next_record` - Position of next record (for pagination)
- `has_more` - Boolean indicating if more results are available
- `query` - Original query string
- `format` - Record format used

### Search Result

The `SearchResult` object contains:

- `record_id` - Unique record identifier
- `title` - Title of the resource
- `author` - Author name(s)
- `year` - Publication year
- `publisher` - Publisher information
- `isbn` - ISBN number
- `raw_data` - Raw XML data
- `format` - Record format

### Scan Response

The `ScanResponse` object contains:

- `terms` - List of `ScanTerm` objects
- `scan_clause` - Original scan clause used
- `response_position` - Starting position in the term list

### Scan Term

The `ScanTerm` object contains:

- `value` - The term value (e.g., "Goethe, Johann Wolfgang von")
- `number_of_records` - Number of records for this term
- `display_term` - Display form of the term (optional, may be None)
- `extra_data` - Additional term data (optional, may be None)

## SRU API Reference

This client uses the SWB SRU interface:

- **Base URL**: `https://sru.k10plus.de/swb`
- **Protocol**: SRU 1.1
- **Query Language**: CQL (Contextual Query Language)

### CQL Search Indices

| Index | CQL Name | Description |
|-------|----------|-------------|
| TITLE | pica.tit | Title search |
| AUTHOR | pica.per | Person/Author search |
| SUBJECT | pica.sub | Subject search |
| ISBN | pica.isb | ISBN number |
| ISSN | pica.iss | ISSN number |
| PUBLISHER | pica.vlg | Publisher search |
| YEAR | pica.ejr | Publication year |
| KEYWORD | pica.woe | Keyword search |
| ALL | pica.all | Search all fields |

## Troubleshooting

### Connection Issues

If you encounter connection timeouts:

```bash
# The client uses a 30-second timeout by default
# For slow connections, you can modify the timeout in code:
from swb import SWBClient

client = SWBClient(timeout=60)  # 60 seconds
```

### SSL Certificate Issues

If you encounter SSL certificate errors, ensure your system's CA certificates are up to date:

```bash
# macOS
brew install ca-certificates

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ca-certificates
```

### No Results Found

If searches return no results:

1. Check your query syntax
2. Try using wildcards: `pica.tit="Pytho*"`
3. Use the `--verbose` flag to see the actual query being sent
4. Test with a broader search term

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`pytest && ruff check .`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Resources

- [SWB Website](https://www.bsz-bw.de/swb.html)
- [K10plus SRU Documentation](https://wiki.k10plus.de/display/K10PLUS/SRU)
- [CQL Specification](https://www.loc.gov/standards/sru/cql/)
- [MARC 21 Format](https://www.loc.gov/marc/bibliographic/)

## Acknowledgments

- Bibliotheksservice-Zentrum Baden-Württemberg (BSZ) for providing the SRU API
- K10plus consortium for the comprehensive library catalog

## Contact

For questions or issues, please open an issue on GitHub or contact the maintainers.
