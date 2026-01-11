# SWB API Client

A Python CLI client for querying the Südwestdeutscher Bibliotheksverbund (SWB) library catalog via the SRU (Search/Retrieve via URL) API.

## Features

- **Interactive Terminal UI (TUI)** - User-friendly interface with keyboard shortcuts for exploring the catalog
- Search the SWB catalog using CQL queries or simple keywords
- Support for multiple search indices (title, author, ISBN, ISSN, etc.)
- **Faceted search (SRU 2.0)** - Filter and explore results by year, author, subject, and other categories
- **Multiple library catalog profiles** - Switch between different German library union catalogs (SWB, K10plus, DNB, GBV, BVB, HeBIS)
- **Library holdings display** - See which libraries have items and access information
- Index scanning for auto-completion and browsing terms
- Server capabilities discovery via SRU explain operation
- Band/linking search for finding related publications in multi-volume works
- Sort results by relevance, year, author, or title
- Multiple output formats (MARCXML, TurboMARC, MODS, PICA, Dublin Core)
- Rich terminal output with formatted tables
- Export search results to files
- Comprehensive error handling and logging
- Type-safe with full mypy support
- Well-tested with pytest (83 tests, 82% API coverage)

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Install from source

```bash
# Clone the repository
git clone https://github.com/jvanvinkenroye/swb.git
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

### Terminal User Interface (TUI)

The SWB client includes an experimental interactive terminal UI powered by Textual:

```bash
# Launch the interactive TUI
swb-tui
```

The TUI provides:
- **Interactive search interface** with real-time results
- **Keyboard shortcuts** for efficient navigation
  - `Ctrl+S` - Execute search
  - `Ctrl+C` - Clear results
  - `Ctrl+Q` - Quit application
- **Dropdown menus** for search indices and record formats
- **Formatted results display** in scrollable containers
- **Error handling** with helpful messages

The TUI is perfect for exploring the catalog interactively without memorizing CLI commands.

### Command Line Interface (CLI)

#### Basic Search

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
swb search "Python" --format turbomarc
```

Available formats:
- `marcxml` (default) - MARC 21 XML format
- `marcxml-legacy` - MARC 21 XML Legacy format
- `turbomarc` - TurboMARC (optimized XML for MARC records)
- `mods` - Metadata Object Description Schema
- `mods36` - MODS version 3.6
- `picaxml` - PICA XML format
- `dc` - Dublin Core
- `isbd` - International Standard Bibliographic Description
- `mads` - Metadata Authority Description Schema

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

#### Faceted Search (SRU 2.0)

**Note**: Faceted search requires SRU 2.0 support from the server. The client automatically switches to SRU 2.0 when facets are requested.

Use facets to explore result distribution and filter by categories:

```bash
# Get faceted results by year and author
swb search "Python" --facets year,author

# Get more facet values (default is 10)
swb search "Python" --facets year,author,subject --facet-limit 20

# Combine with other options
swb search "Machine Learning" --index title --facets year --facet-limit 15 --max 20
```

Faceted search allows you to:
- **See distribution**: Understand how results are distributed across years, authors, subjects
- **Explore data**: Discover patterns in the search results
- **Navigate results**: Find the most common values in each category

Example output shows facets like:
- **Years**: 2024 (45), 2023 (38), 2022 (27)
- **Authors**: Van Rossum, Guido (12), Lutz, Mark (8)
- **Subjects**: Programming (89), Data Science (34)

Common facet fields (availability depends on server support):
- `year` - Publication year
- `author` - Author names
- `subject` - Subject headings
- `language` - Language codes
- `format` - Material/format type

**Compatibility**: Not all SRU servers support faceting. If the server doesn't support SRU 2.0 or faceting, the facets field will be empty (None) in the response.

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

#### Library Catalog Profiles

The SWB client supports multiple German library union catalogs through pre-configured profiles. This allows you to search different catalogs without manually specifying endpoint URLs.

**List available profiles:**
```bash
swb profiles
```

**Available profiles:**
- **swb** - SWB (Südwestdeutscher Bibliotheksverbund) - Baden-Württemberg, Saarland, Sachsen
- **k10plus** - K10plus Verbundkatalog - Northern and southwestern Germany (includes many NRW libraries)
- **gvk** - GBV (Gemeinsamer Verbundkatalog) - Northern Germany
- **dnb** - DNB (Deutsche Nationalbibliothek) - German National Library
- **bvb** - BVB (Bibliotheksverbund Bayern) - Bavaria
- **hebis** - HeBIS (Hessisches BibliotheksInformationsSystem) - Hesse and parts of Rhineland-Palatinate

**Use a specific profile:**
```bash
# Search K10plus catalog
swb search "Python programming" --profile k10plus

# Search DNB catalog
swb isbn 978-3-16-148410-0 --profile dnb

# Search with profile shorthand
swb search "Goethe" -p gvk --max 10
```

**Profile priority:**
1. Custom `--url` option (overrides profile)
2. `--profile` option
3. Default profile (swb)

**Example with custom URL:**
```bash
# Custom URL takes precedence over profile
swb search "query" --profile k10plus --url https://custom.endpoint.de/sru
```

**Compatible with all commands:**
The `--profile` option works with all search commands: `search`, `isbn`, `issn`, `related`, `scan`, `explain`.

#### Library Holdings

Display library holdings information showing which libraries have the item and how to access it:

```bash
# Show holdings for an ISBN search
swb isbn 978-3-17-025295-0 --holdings

# Show holdings for a title search
swb search "Sozialtraining für Menschen im Autismus-Spektrum" --holdings

# Combine with other options
swb search "Python programming" --index title --holdings --max 5
```

The `--holdings` option displays:
- **Library locations**: Which institutions hold the item
- **Collections**: Specific collections or call numbers
- **Access information**:
  - Online access URLs for electronic resources
  - Access restrictions (VPN required, campus network only, etc.)
  - Usage notes and availability

**Example holdings output:**
```
Library Holdings:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Library                      ┃ Collection      ┃ Access             ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Universität Tübingen (DE-21) │ E-Book          │ Online Access      │
│                              │ Kohlhammer      │ Campus/VPN only    │
│ UB Rostock (DE-15)           │ N/A             │ Online Access      │
└──────────────────────────────┴─────────────────┴────────────────────┘
```

**Available with:**
- `swb search` - Search commands
- `swb isbn` - ISBN searches
- `swb issn` - ISSN searches
- `swb related` - Related records

**Note**: Holdings information is only available for records that include MARC field 924 (local library data). Not all records may have holdings information.

#### Save Results to File

Export search results:

```bash
swb search "Python" --output results.txt
swb search "Python" --output results.txt --raw  # Include raw XML
```

#### Record Packing Mode

Control how records are returned from the server:

```bash
# Default: XML packing (records embedded as XML)
swb search "Python" --packing xml

# String packing (records escaped as strings)
swb search "Python" --packing string
```

Available packing modes:
- `xml` (default) - Records embedded as XML in the response (parsed and displayed)
- `string` - Records escaped as strings in the response (returned as raw escaped XML)

**Note**: String packing returns raw escaped XML strings without parsing. This mode is useful for:
- Debugging and logging raw records
- Integration with systems expecting string data
- Custom XML processing

Most users should use the default `xml` packing mode.

#### Verbosity Control

```bash
# Verbose output (DEBUG level)
swb --verbose search "Python"

# Quiet mode (errors only)
swb --quiet search "Python"
```

### Band/Linking Search (Related Publications)

Search for records related to a specific publication, useful for multi-volume works and series:

```bash
# Find all volumes (child records) of a multi-volume work
swb related 267838395 --relation-type child

# Find the parent record of a volume
swb related 123456789 --relation-type parent

# Find entire family of related records
swb related 267838395 --relation-type family --max 50

# Find related records (non-hierarchical)
swb related 111222333 --relation-type related

# Find thesaurus-related records
swb related 444555666 --relation-type thesaurus
```

Available relationship types:
- `child` - Find child records (e.g., volumes in a multi-volume work)
- `parent` - Find parent records (e.g., the main entry for a volume)
- `family` - Find all related records in the family
- `related` - Find non-hierarchical related records
- `thesaurus` - Find thesaurus-related records

You can also specify the record type:
```bash
# Search for related authority records
swb related 111222333 --relation-type related --record-type authority
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

### Server Capabilities (Explain)

Get detailed information about the SRU server's capabilities:

```bash
swb explain
```

This displays:
- **Server Information**: Host, port, database name
- **Database Information**: Title, description, contact
- **Supported Record Formats**: All available output formats (MARCXML, MODS, TurboMARC, etc.)
- **Available Search Indices**: All searchable fields with their CQL names (256+ indices)

The explain operation is useful for:
- Discovering available search indices
- Finding supported record formats
- Understanding server configuration
- Programmatic service discovery

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
swb related --help
swb scan --help
swb explain --help
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
│       ├── models.py        # Data models
│       ├── profiles.py      # Library catalog profiles
│       └── tui.py           # Terminal user interface
├── tests/
│   ├── __init__.py
│   ├── test_api.py          # API client tests
│   ├── test_cli.py          # CLI tests
│   ├── test_models.py       # Model tests
│   └── test_profiles.py     # Profile tests
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

    # Search with TurboMARC format (optimized for XSLT processing)
    response = client.search(
        "Python",
        index=SearchIndex.TITLE,
        record_format=RecordFormat.TURBOMARC,
        maximum_records=10
    )

    # Search with additional formats
    response = client.search(
        "Python",
        index=SearchIndex.TITLE,
        record_format=RecordFormat.MARCXML_LEGACY,
        maximum_records=10
    )
    response = client.search(
        "Python",
        index=SearchIndex.TITLE,
        record_format=RecordFormat.MODS36,
        maximum_records=10
    )
    response = client.search(
        "Python",
        index=SearchIndex.TITLE,
        record_format=RecordFormat.MADS,
        maximum_records=10
    )

    # Search with string packing (returns raw escaped XML)
    response = client.search(
        "Python",
        index=SearchIndex.TITLE,
        record_packing="string"
    )
    # Note: String-packed records contain raw escaped XML in result.raw_data
    # without parsed title, author, etc. fields

    # Search by ISBN
    response = client.search_by_isbn("978-3-16-148410-0")

    # Search by ISSN
    response = client.search_by_issn("0028-0836")

    # Search for related records (band/linking search)
    from swb import RelationType, RecordType

    # Find child records (volumes) of a multi-volume work
    related_response = client.search_related(
        ppn="267838395",
        relation_type=RelationType.CHILD,
        maximum_records=20
    )

    # Find parent record
    parent_response = client.search_related(
        ppn="123456789",
        relation_type=RelationType.PARENT,
    )

    # Find entire family of related records
    family_response = client.search_related(
        ppn="267838395",
        relation_type=RelationType.FAMILY,
        record_type=RecordType.BIBLIOGRAPHIC,
        maximum_records=50
    )

    # Scan index for terms (auto-completion)
    scan_response = client.scan(
        scan_clause="pica.per=Goe",
        maximum_terms=10,
        response_position=1
    )

    # Get server capabilities
    explain_response = client.explain()
    print(f"Server: {explain_response.server_info.host}")
    print(f"Database: {explain_response.database_info.title}")
    print(f"Supported formats: {len(explain_response.schemas)}")
    print(f"Available indices: {len(explain_response.indices)}")

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

### Explain Response

The `ExplainResponse` object contains:

- `server_info` - ServerInfo object with server details
- `database_info` - DatabaseInfo object with database details
- `indices` - List of IndexInfo objects (available search indices)
- `schemas` - List of SchemaInfo objects (supported record formats)

### Server Info

The `ServerInfo` object contains:

- `host` - Server hostname
- `port` - Server port (optional, may be None)
- `database` - Database name (optional, may be None)

### Database Info

The `DatabaseInfo` object contains:

- `title` - Database title
- `description` - Database description (optional, may be None)
- `contact` - Contact information (optional, may be None)

### Index Info

The `IndexInfo` object contains:

- `title` - Human-readable index title
- `name` - CQL index name (e.g., "pica.tit", "pica.per")
- `description` - Index description (optional, may be None)

### Schema Info

The `SchemaInfo` object contains:

- `identifier` - Schema identifier (e.g., "marcxml", "mods")
- `name` - Schema name
- `title` - Schema title (optional, may be None)

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
