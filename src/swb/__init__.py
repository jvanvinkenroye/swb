"""SWB API Client - A Python client for the Südwestdeutscher Bibliotheksverbund (SWB) API."""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from swb.api import SWBClient
from swb.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    ParseError,
    RateLimitError,
    ServerError,
    SWBError,
    ValidationError,
)
from swb.models import (
    DatabaseInfo,
    ExplainResponse,
    IndexInfo,
    RecordFormat,
    RecordType,
    RelationType,
    ScanResponse,
    ScanTerm,
    SchemaInfo,
    SearchIndex,
    SearchResponse,
    SearchResult,
    ServerInfo,
    SortBy,
    SortOrder,
)

__all__ = [
    "SWBClient",
    # Exceptions
    "SWBError",
    "APIError",
    "AuthenticationError",
    "ConfigurationError",
    "NetworkError",
    "ParseError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    # Models
    "DatabaseInfo",
    "ExplainResponse",
    "IndexInfo",
    "RecordFormat",
    "RecordType",
    "RelationType",
    "ScanResponse",
    "ScanTerm",
    "SchemaInfo",
    "SearchIndex",
    "SearchResponse",
    "SearchResult",
    "ServerInfo",
    "SortBy",
    "SortOrder",
]

# Optional TUI imports (requires textual extra)
try:
    from swb.tui import SWBTUIDirect, run_tui

    __all__.extend(["run_tui", "SWBTUIDirect"])
except ImportError:
    # TUI dependencies not installed
    pass
