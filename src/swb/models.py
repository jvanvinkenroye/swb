"""Data models for SWB API."""

from dataclasses import dataclass
from enum import Enum


class RecordFormat(str, Enum):
    """Supported record formats for SRU queries."""

    MARCXML = "marcxml"
    MARCXML_LEGACY = "marcxml-legacy"
    MODS = "mods"
    MODS36 = "mods36"
    PICA = "picaxml"
    DUBLIN_CORE = "dc"
    ISBD = "isbd"
    TURBOMARC = "turbomarc"
    MADS = "mads"


class SearchIndex(str, Enum):
    """Available search indices for CQL queries."""

    TITLE = "pica.tit"
    AUTHOR = "pica.per"
    SUBJECT = "pica.sub"
    ISBN = "pica.isb"
    ISSN = "pica.iss"
    PUBLISHER = "pica.vlg"
    YEAR = "pica.ejr"
    ALL = "pica.all"
    KEYWORD = "pica.woe"


class SortBy(str, Enum):
    """Available sort options for search results."""

    RELEVANCE = "relevance"
    YEAR = "year"
    AUTHOR = "author"
    TITLE = "title"


class SortOrder(str, Enum):
    """Sort order options."""

    ASCENDING = "ascending"
    DESCENDING = "descending"


class RelationType(str, Enum):
    """Record relationship types for band/linking search.

    Used to find related publications in multi-volume works.
    """

    FAMILY = "fam"  # Find entire family - all related records
    PARENT = "rel-bt"  # Parent records (broader term)
    CHILD = "rel-nt"  # Child records (narrower term)
    RELATED = "rel-rt"  # Non-hierarchical related records
    THESAURUS = "rel-tt"  # Thesaurus-related records


class RecordType(str, Enum):
    """Record types for filtering searches."""

    BIBLIOGRAPHIC = "b"  # Bibliographic records (titles)
    AUTHORITY = "n"  # Authority records (names, subjects)


@dataclass
class LibraryHolding:
    """Represents library holding information for a record.

    Attributes:
        library_code: Library identifier code (e.g., DE-21, DE-15)
        library_name: Human-readable library name
        access_url: URL for accessing the resource at this library
        access_note: Note about access restrictions or requirements
        collection: Collection or database name
    """

    library_code: str
    library_name: str | None = None
    access_url: str | None = None
    access_note: str | None = None
    collection: str | None = None


@dataclass
class SearchResult:
    """Represents a single search result from the SWB API.

    Attributes:
        record_id: Unique identifier for the record
        title: Title of the resource
        author: Author(s) of the resource
        year: Publication year
        publisher: Publisher information
        isbn: ISBN number(s)
        raw_data: Raw XML data from the API
        format: Format of the record data
        holdings: List of library holdings for this record
    """

    record_id: str | None = None
    title: str | None = None
    author: str | None = None
    year: str | None = None
    publisher: str | None = None
    isbn: str | None = None
    raw_data: str | None = None
    format: RecordFormat = RecordFormat.MARCXML
    holdings: list[LibraryHolding] = None  # type: ignore

    def __post_init__(self) -> None:
        """Initialize mutable default values."""
        if self.holdings is None:
            self.holdings = []


@dataclass
class FacetValue:
    """A single facet value with count.

    Attributes:
        value: The facet value (e.g., "2024", "Python Programming")
        count: Number of results with this value
    """

    value: str
    count: int


@dataclass
class Facet:
    """A facet category with values.

    Attributes:
        name: Facet field name (e.g., "year", "author", "subject")
        values: List of facet values with counts
    """

    name: str
    values: list[FacetValue]


@dataclass
class SearchResponse:
    """Represents the complete response from an SRU search query.

    Attributes:
        total_results: Total number of results found
        results: List of individual search results
        next_record: Position of the next record for pagination
        query: Original CQL query string
        format: Record format used
        facets: List of facets (only available with SRU 2.0)
    """

    total_results: int
    results: list[SearchResult]
    next_record: int | None = None
    query: str = ""
    format: RecordFormat = RecordFormat.MARCXML
    facets: list[Facet] | None = None

    @property
    def has_more(self) -> bool:
        """Check if there are more results available."""
        return self.next_record is not None and self.next_record <= self.total_results


@dataclass
class ScanTerm:
    """Represents a single term from a scan operation.

    Attributes:
        value: The term value
        number_of_records: Number of records containing this term
        display_term: Human-readable display form of the term
        extra_data: Additional term metadata
    """

    value: str
    number_of_records: int
    display_term: str | None = None
    extra_data: str | None = None


@dataclass
class ScanResponse:
    """Represents the response from an SRU scan operation.

    Attributes:
        terms: List of scan terms
        scan_clause: Original scan clause
        response_position: Position in the term list
    """

    terms: list[ScanTerm]
    scan_clause: str
    response_position: int = 1


@dataclass
class IndexInfo:
    """Information about a searchable index.

    Attributes:
        title: Index title/name
        name: Index identifier (CQL name)
        description: Optional description of the index
    """

    title: str
    name: str
    description: str | None = None


@dataclass
class SchemaInfo:
    """Information about a record schema format.

    Attributes:
        identifier: Schema identifier (e.g., "marcxml", "mods")
        name: Human-readable schema name
        title: Optional schema title
    """

    identifier: str
    name: str
    title: str | None = None


@dataclass
class DatabaseInfo:
    """Information about the SRU database.

    Attributes:
        title: Database title
        description: Database description
        contact: Contact information
    """

    title: str
    description: str | None = None
    contact: str | None = None


@dataclass
class ServerInfo:
    """Information about the SRU server.

    Attributes:
        host: Server host
        port: Server port
        database: Database name
    """

    host: str
    port: int | None = None
    database: str | None = None


@dataclass
class ExplainResponse:
    """Represents the response from an SRU explain operation.

    The explain operation provides information about the server's capabilities,
    including available search indices, supported record formats, and database
    information.

    Attributes:
        server_info: Information about the server
        database_info: Information about the database
        indices: List of available search indices
        schemas: List of supported record schemas
    """

    server_info: ServerInfo
    database_info: DatabaseInfo
    indices: list[IndexInfo]
    schemas: list[SchemaInfo]
