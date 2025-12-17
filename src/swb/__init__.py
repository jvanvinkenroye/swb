"""SWB API Client - A Python client for the Südwestdeutscher Bibliotheksverbund (SWB) API."""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from swb.api import SWBClient
from swb.models import (
    DatabaseInfo,
    ExplainResponse,
    IndexInfo,
    RecordFormat,
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
    "DatabaseInfo",
    "ExplainResponse",
    "IndexInfo",
    "RecordFormat",
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
