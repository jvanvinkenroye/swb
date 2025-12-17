"""Data models for SWB API."""

from dataclasses import dataclass
from enum import Enum


class RecordFormat(str, Enum):
    """Supported record formats for SRU queries."""

    MARCXML = "marcxml"
    MODS = "mods"
    PICA = "picaxml"
    DUBLIN_CORE = "dc"
    ISBD = "isbd"


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
    """

    record_id: str | None = None
    title: str | None = None
    author: str | None = None
    year: str | None = None
    publisher: str | None = None
    isbn: str | None = None
    raw_data: str | None = None
    format: RecordFormat = RecordFormat.MARCXML


@dataclass
class SearchResponse:
    """Represents the complete response from an SRU search query.

    Attributes:
        total_results: Total number of results found
        results: List of individual search results
        next_record: Position of the next record for pagination
        query: Original CQL query string
        format: Record format used
    """

    total_results: int
    results: list[SearchResult]
    next_record: int | None = None
    query: str = ""
    format: RecordFormat = RecordFormat.MARCXML

    @property
    def has_more(self) -> bool:
        """Check if there are more results available."""
        return self.next_record is not None and self.next_record <= self.total_results
