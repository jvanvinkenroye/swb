"""SWB API Client - A Python client for the Südwestdeutscher Bibliotheksverbund (SWB) API."""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from swb.api import SWBClient
from swb.models import (
    RecordFormat,
    ScanResponse,
    ScanTerm,
    SearchIndex,
    SearchResponse,
    SearchResult,
    SortBy,
    SortOrder,
)

__all__ = [
    "SWBClient",
    "RecordFormat",
    "ScanResponse",
    "ScanTerm",
    "SearchIndex",
    "SearchResponse",
    "SearchResult",
    "SortBy",
    "SortOrder",
]
