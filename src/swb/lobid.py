"""Client for the lobid-resources API (hbz union catalog, NRW).

The hbz (Hochschulbibliothekszentrum NRW) has no public SRU endpoint since
the Aleph union database was shut down end of 2024 (Alma migration). Its
official open interface is lobid-resources (https://lobid.org/resources/api):
a JSON-LD web API with Lucene query syntax, no authentication, CC0-licensed.

This client maps lobid responses onto the same models the SRU client uses
(SearchResult, LibraryHolding, SearchResponse) so the CLI display code works
unchanged. SRU-only operations (scan, explain, related) raise ValidationError.
"""

import json
import logging
from types import TracebackType
from typing import Any

import requests

from swb.exceptions import (
    APIError,
    NetworkError,
    ParseError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from swb.models import (
    LibraryHolding,
    SearchIndex,
    SearchResponse,
    SearchResult,
)

logger = logging.getLogger(__name__)

DEFAULT_LOBID_URL = "https://lobid.org/resources"

# Maps the CLI's SearchIndex values onto lobid/Lucene field names.
# ALL and KEYWORD are handled as plain full-text queries (no field prefix).
LOBID_FIELDS: dict[SearchIndex, str] = {
    SearchIndex.TITLE: "title",
    SearchIndex.AUTHOR: "contribution.agent.label",
    SearchIndex.SUBJECT: "subjectslabels",
    SearchIndex.ISBN: "isbn",
    SearchIndex.ISSN: "issn",
    SearchIndex.PUBLISHER: "publication.publishedBy",
    SearchIndex.YEAR: "publication.startDate",
}


class LobidClient:
    """Client for the lobid-resources JSON API.

    Provides the subset of the SWBClient interface that the lobid API can
    serve: search, search_by_isbn, search_by_issn. Holdings are always
    parsed (lobid delivers them inline under "hasItem").

    Args:
        base_url: API base URL (default: https://lobid.org/resources)
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.base_url = (base_url or DEFAULT_LOBID_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def __enter__(self) -> "LobidClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def search(
        self,
        query: str,
        *,
        index: SearchIndex | None = None,
        start_record: int = 1,
        maximum_records: int = 10,
        sort_by: Any = None,
        sort_order: Any = None,
        record_format: Any = None,
        record_packing: Any = None,
        facets: list[str] | None = None,
        facet_limit: int = 10,
        owner: str | None = None,
    ) -> SearchResponse:
        """Search the hbz catalog via lobid-resources.

        Args:
            query: Search terms, or a raw Lucene query when no index is given
            index: Search index; mapped to a lobid field (see LOBID_FIELDS)
            start_record: 1-based start position (lobid "from" is 0-based)
            maximum_records: Number of records to return
            sort_by: Not supported by the lobid backend (raises ValidationError)
            sort_order: Accepted for CLI compatibility, ignored without sort_by
            record_format: Accepted for CLI compatibility, ignored (JSON only)
            record_packing: Accepted for CLI compatibility, ignored
            facets: Not supported by the lobid backend (raises ValidationError)
            facet_limit: Accepted for CLI compatibility, ignored
            owner: Optional comma-separated ISIL list to filter by holdings

        Returns:
            SearchResponse with results mapped to the shared models

        Raises:
            ValidationError: Invalid parameters or unsupported options
        """
        if not query or not query.strip():
            raise ValidationError("Query cannot be empty")
        if start_record < 1:
            raise ValidationError("start_record must be >= 1")
        if maximum_records < 1:
            raise ValidationError("maximum_records must be >= 1")
        if sort_by is not None:
            raise ValidationError(
                "Sorting is not supported by the lobid backend (hbz). "
                "Omit --sort-by or use an SRU profile such as k10plus."
            )
        if facets:
            raise ValidationError(
                "Facets are not supported by the lobid backend (hbz). "
                "Omit --facets or use an SRU profile such as k10plus."
            )

        q = self._build_query(query, index)
        params: dict[str, str | int] = {
            "q": q,
            "from": start_record - 1,
            "size": maximum_records,
            "format": "json",
        }
        if owner:
            params["owner"] = owner

        data = self._get_json(f"{self.base_url}/search", params)
        return self._parse_search_response(data, q, start_record)

    def search_by_isbn(
        self,
        isbn: str,
        *,
        record_format: Any = None,
        record_packing: Any = None,
    ) -> SearchResponse:
        """Search by ISBN (hyphens and spaces are stripped)."""
        cleaned = isbn.replace("-", "").replace(" ", "")
        if not cleaned:
            raise ValidationError("ISBN cannot be empty")
        return self.search(cleaned, index=SearchIndex.ISBN)

    def search_by_issn(
        self,
        issn: str,
        *,
        record_format: Any = None,
        record_packing: Any = None,
    ) -> SearchResponse:
        """Search by ISSN (hyphens and spaces are stripped).

        Note: lobid stores ISSNs without hyphens.
        """
        cleaned = issn.replace("-", "").replace(" ", "")
        if not cleaned:
            raise ValidationError("ISSN cannot be empty")
        return self.search(cleaned, index=SearchIndex.ISSN)

    def scan(self, *args: Any, **kwargs: Any) -> Any:
        """Not supported: lobid has no SRU scan operation."""
        raise ValidationError(
            "Scan is not supported by the lobid backend (hbz). "
            "Use an SRU profile such as k10plus: "
            'swb scan "pica.tit=..." --profile k10plus'
        )

    def explain(self, *args: Any, **kwargs: Any) -> Any:
        """Not supported: lobid has no SRU explain operation."""
        raise ValidationError(
            "Explain is not supported by the lobid backend (hbz). "
            "See https://lobid.org/resources/api for the API description."
        )

    def search_related(self, *args: Any, **kwargs: Any) -> Any:
        """Not supported: lobid has no PPN-based relation search."""
        raise ValidationError(
            "Related-records search is not supported by the lobid backend "
            "(hbz). Use an SRU profile such as k10plus."
        )

    def _build_query(self, query: str, index: SearchIndex | None) -> str:
        """Translate query plus index into a lobid Lucene query string."""
        if index is None or index in (SearchIndex.ALL, SearchIndex.KEYWORD):
            return query
        field = LOBID_FIELDS.get(index)
        if field is None:
            raise ValidationError(
                f"Index {index.name} is not supported by the lobid backend"
            )
        escaped = query.replace('"', '\\"')
        return f'{field}:"{escaped}"'

    def _get_json(
        self, url: str, params: dict[str, str | int]
    ) -> dict[str, Any]:
        """Perform a GET request and return the decoded JSON body."""
        logger.debug("lobid request: %s params=%s", url, params)
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except (requests.ConnectionError, requests.Timeout) as e:
            raise NetworkError(f"Connection to lobid API failed: {e}") from e
        except requests.RequestException as e:
            raise NetworkError(f"Request to lobid API failed: {e}") from e

        if response.status_code == 429:
            raise RateLimitError(
                "lobid API rate limit exceeded", status_code=429
            )
        if response.status_code >= 500:
            raise ServerError(
                f"lobid API server error (HTTP {response.status_code})",
                status_code=response.status_code,
            )
        if response.status_code != 200:
            raise APIError(
                f"lobid API returned HTTP {response.status_code}",
                status_code=response.status_code,
            )

        try:
            result: dict[str, Any] = response.json()
        except ValueError as e:
            raise ParseError(
                f"Invalid JSON from lobid API: {e}",
                xml_snippet=response.text[:200],
            ) from e
        return result

    def _parse_search_response(
        self, data: dict[str, Any], query: str, start_record: int
    ) -> SearchResponse:
        """Map a lobid search response onto SearchResponse."""
        total = int(data.get("totalItems", 0))
        members = data.get("member", [])
        results = [self._parse_member(m) for m in members]

        next_record: int | None = None
        if results and start_record + len(results) <= total:
            next_record = start_record + len(results)

        return SearchResponse(
            total_results=total,
            results=results,
            next_record=next_record,
            query=query,
        )

    def _parse_member(self, member: dict[str, Any]) -> SearchResult:
        """Map one lobid member (JSON-LD resource) onto SearchResult."""
        title = member.get("title")
        subtitle_list = member.get("otherTitleInformation") or []
        if title and subtitle_list:
            title = f"{title} : {subtitle_list[0]}"

        publications = member.get("publication") or []
        publication = publications[0] if publications else {}
        year = publication.get("startDate") or publication.get("dateStatement")
        published_by = publication.get("publishedBy") or []
        publisher = ", ".join(published_by) if published_by else None

        isbn_list = member.get("isbn") or []
        isbn = ", ".join(isbn_list) if isbn_list else None

        link = member.get("id")

        return SearchResult(
            record_id=member.get("almaMmsId") or member.get("hbzId"),
            title=title,
            author=self._extract_author(member),
            year=year,
            publisher=publisher,
            isbn=isbn,
            raw_data=json.dumps(member, ensure_ascii=False, indent=2),
            holdings=self._extract_holdings(member),
            link=link,
        )

    @staticmethod
    def _extract_author(member: dict[str, Any]) -> str | None:
        """Pick contributor labels, preferring the author role (aut)."""
        contributions = member.get("contribution") or []
        authors = [
            c
            for c in contributions
            if c.get("role", {}).get("id", "").rsplit("/", 1)[-1] == "aut"
        ] or contributions
        labels = [
            label
            for c in authors
            if (label := c.get("agent", {}).get("label"))
        ]
        return "; ".join(labels[:3]) if labels else None

    @staticmethod
    def _extract_holdings(member: dict[str, Any]) -> list[LibraryHolding]:
        """Map lobid hasItem entries onto LibraryHolding."""
        holdings = []
        for item in member.get("hasItem") or []:
            held_by = item.get("heldBy") or {}
            see_also = item.get("seeAlso") or []
            call_number = item.get("callNumber")
            holdings.append(
                LibraryHolding(
                    library_code=held_by.get("isil") or "",
                    library_name=held_by.get("label"),
                    access_url=see_also[0] if see_also else None,
                    access_note=(
                        f"Signatur: {call_number}" if call_number else None
                    ),
                )
            )
        return holdings
