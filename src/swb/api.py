"""SRU API client for the Südwestdeutscher Bibliotheksverbund (SWB)."""

import logging
from types import TracebackType

import requests
from lxml import etree

from swb.models import (
    RecordFormat,
    SearchIndex,
    SearchResponse,
    SearchResult,
    SortBy,
    SortOrder,
)

logger = logging.getLogger(__name__)


class SWBClient:
    """Client for interacting with the SWB SRU API.

    The SWB (Südwestdeutscher Bibliotheksverbund) provides an SRU
    (Search/Retrieve via URL) interface for searching library catalogs.

    Attributes:
        base_url: Base URL for the SRU endpoint
        timeout: Request timeout in seconds
        session: Requests session for connection pooling
    """

    DEFAULT_BASE_URL = "https://sru.k10plus.de/swb"
    SRU_VERSION = "1.1"

    # XML namespaces used in SRU responses
    NAMESPACES = {
        "srw": "http://www.loc.gov/zing/srw/",
        "marc": "http://www.loc.gov/MARC21/slim",
        "mods": "http://www.loc.gov/mods/v3",
        "dc": "http://purl.org/dc/elements/1.1/",
        "pica": "info:srw/schema/5/picaXML-v1.0",
    }

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = 30,
    ) -> None:
        """Initialize the SWB API client.

        Args:
            base_url: Custom base URL for the SRU endpoint.
                     Defaults to the official SWB endpoint.
            timeout: Request timeout in seconds. Defaults to 30.
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "SWB-Python-Client/0.1.0",
            }
        )

    def search(
        self,
        query: str,
        record_format: RecordFormat = RecordFormat.MARCXML,
        start_record: int = 1,
        maximum_records: int = 10,
        index: SearchIndex | None = None,
        sort_by: SortBy | None = None,
        sort_order: SortOrder = SortOrder.DESCENDING,
    ) -> SearchResponse:
        """Search the SWB catalog using CQL query syntax.

        Args:
            query: Search query. Can be a simple keyword or full CQL query.
            record_format: Desired format for the results.
            start_record: Position of first record to return (1-based).
            maximum_records: Maximum number of records to return.
            index: Search index to use. If provided, query is treated as
                  a simple keyword search in that index.
            sort_by: Sort results by relevance, year, author, or title.
            sort_order: Sort order (ascending or descending). Default is descending.

        Returns:
            SearchResponse containing the search results.

        Raises:
            requests.RequestException: If the API request fails.
            ValueError: If the response cannot be parsed.

        Example:
            >>> client = SWBClient()
            >>> results = client.search(
            ...     "Python",
            ...     index=SearchIndex.TITLE,
            ...     sort_by=SortBy.YEAR,
            ...     sort_order=SortOrder.DESCENDING
            ... )
            >>> print(f"Found {results.total_results} results")
        """
        # Build CQL query if index is specified
        if index:
            cql_query = f'{index.value}="{query}"'
        else:
            cql_query = query

        params = {
            "version": self.SRU_VERSION,
            "operation": "searchRetrieve",
            "query": cql_query,
            "recordSchema": record_format.value,
            "startRecord": start_record,
            "maximumRecords": maximum_records,
        }

        # Add sorting if specified
        # sortKeys format: <field>,,<order> where order: 0=descending, 1=ascending
        if sort_by:
            sort_order_value = "1" if sort_order == SortOrder.ASCENDING else "0"
            params["sortKeys"] = f"{sort_by.value},,{sort_order_value}"

        logger.info(f"Searching SWB: {cql_query}")
        logger.debug(f"Request parameters: {params}")

        try:
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            # Ensure UTF-8 encoding for proper handling of German umlauts
            response.encoding = "utf-8"
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

        return self._parse_response(response.text, cql_query, record_format)

    def search_by_isbn(
        self,
        isbn: str,
        record_format: RecordFormat = RecordFormat.MARCXML,
    ) -> SearchResponse:
        """Search for a book by ISBN.

        Args:
            isbn: ISBN number (with or without hyphens).
            record_format: Desired format for the results.

        Returns:
            SearchResponse containing the search results.
        """
        # Remove common ISBN separators
        clean_isbn = isbn.replace("-", "").replace(" ", "")
        return self.search(
            clean_isbn,
            record_format=record_format,
            index=SearchIndex.ISBN,
        )

    def search_by_issn(
        self,
        issn: str,
        record_format: RecordFormat = RecordFormat.MARCXML,
    ) -> SearchResponse:
        """Search for a periodical by ISSN.

        Args:
            issn: ISSN number (with or without hyphens).
            record_format: Desired format for the results.

        Returns:
            SearchResponse containing the search results.
        """
        clean_issn = issn.replace("-", "").replace(" ", "")
        return self.search(
            clean_issn,
            record_format=record_format,
            index=SearchIndex.ISSN,
        )

    def _parse_response(
        self,
        xml_data: str,
        query: str,
        record_format: RecordFormat,
    ) -> SearchResponse:
        """Parse the SRU XML response.

        Args:
            xml_data: Raw XML response from the API.
            query: Original query string.
            record_format: Format of the records.

        Returns:
            Parsed SearchResponse object.

        Raises:
            ValueError: If the XML cannot be parsed or is invalid.
        """
        try:
            # Encode string to UTF-8 bytes for lxml parsing
            # This preserves German umlauts and other special characters
            xml_bytes = (
                xml_data.encode("utf-8") if isinstance(xml_data, str) else xml_data
            )
            root = etree.fromstring(xml_bytes)
        except etree.XMLSyntaxError as e:
            logger.error(f"Failed to parse XML response: {e}")
            raise ValueError(f"Invalid XML response: {e}") from e

        # Extract total number of results
        total_results_elem = root.find(
            ".//srw:numberOfRecords",
            namespaces=self.NAMESPACES,
        )
        total_results = (
            int(total_results_elem.text) if total_results_elem is not None else 0
        )

        # Extract next record position for pagination
        next_record_elem = root.find(
            ".//srw:nextRecordPosition",
            namespaces=self.NAMESPACES,
        )
        next_record = (
            int(next_record_elem.text) if next_record_elem is not None else None
        )

        # Parse individual records
        records = root.findall(".//srw:record", namespaces=self.NAMESPACES)
        results = []

        for record in records:
            result = self._parse_record(record, record_format)
            if result:
                results.append(result)

        logger.info(f"Parsed {len(results)} records from response")

        return SearchResponse(
            total_results=total_results,
            results=results,
            next_record=next_record,
            query=query,
            format=record_format,
        )

    def _parse_record(
        self,
        record_elem: etree._Element,
        record_format: RecordFormat,
    ) -> SearchResult | None:
        """Parse a single record from the SRU response.

        Args:
            record_elem: XML element containing the record.
            record_format: Format of the record.

        Returns:
            Parsed SearchResult or None if parsing fails.
        """
        # Get raw record data
        record_data_elem = record_elem.find(
            ".//srw:recordData",
            namespaces=self.NAMESPACES,
        )

        if record_data_elem is None:
            logger.warning("Record without recordData found")
            return None

        # Convert record data to string
        raw_data = etree.tostring(
            record_data_elem[0],
            encoding="unicode",
            pretty_print=True,
        )

        # Parse based on format
        if record_format == RecordFormat.MARCXML:
            return self._parse_marcxml(record_data_elem, raw_data)
        elif record_format == RecordFormat.MODS:
            return self._parse_mods(record_data_elem, raw_data)
        else:
            # For other formats, just return raw data
            return SearchResult(raw_data=raw_data, format=record_format)

    def _parse_marcxml(
        self,
        record_elem: etree._Element,
        raw_data: str,
    ) -> SearchResult:
        """Parse MARCXML formatted record.

        Args:
            record_elem: XML element containing MARC data.
            raw_data: Raw XML string.

        Returns:
            Parsed SearchResult.
        """
        result = SearchResult(raw_data=raw_data, format=RecordFormat.MARCXML)

        # Extract record ID (MARC 001)
        controlfield_001 = record_elem.find(
            ".//marc:controlfield[@tag='001']",
            namespaces=self.NAMESPACES,
        )
        if controlfield_001 is not None:
            result.record_id = controlfield_001.text

        # Extract title (MARC 245$a)
        title_field = record_elem.find(
            ".//marc:datafield[@tag='245']/marc:subfield[@code='a']",
            namespaces=self.NAMESPACES,
        )
        if title_field is not None:
            result.title = title_field.text

        # Extract author (MARC 100$a or 700$a)
        author_field = record_elem.find(
            ".//marc:datafield[@tag='100']/marc:subfield[@code='a']",
            namespaces=self.NAMESPACES,
        )
        if author_field is None:
            author_field = record_elem.find(
                ".//marc:datafield[@tag='700']/marc:subfield[@code='a']",
                namespaces=self.NAMESPACES,
            )
        if author_field is not None:
            result.author = author_field.text

        # Extract publication year (MARC 264$c or 260$c)
        year_field = record_elem.find(
            ".//marc:datafield[@tag='264']/marc:subfield[@code='c']",
            namespaces=self.NAMESPACES,
        )
        if year_field is None:
            year_field = record_elem.find(
                ".//marc:datafield[@tag='260']/marc:subfield[@code='c']",
                namespaces=self.NAMESPACES,
            )
        if year_field is not None:
            result.year = year_field.text

        # Extract publisher (MARC 264$b or 260$b)
        publisher_field = record_elem.find(
            ".//marc:datafield[@tag='264']/marc:subfield[@code='b']",
            namespaces=self.NAMESPACES,
        )
        if publisher_field is None:
            publisher_field = record_elem.find(
                ".//marc:datafield[@tag='260']/marc:subfield[@code='b']",
                namespaces=self.NAMESPACES,
            )
        if publisher_field is not None:
            result.publisher = publisher_field.text

        # Extract ISBN (MARC 020$a)
        isbn_field = record_elem.find(
            ".//marc:datafield[@tag='020']/marc:subfield[@code='a']",
            namespaces=self.NAMESPACES,
        )
        if isbn_field is not None:
            result.isbn = isbn_field.text

        return result

    def _parse_mods(
        self,
        record_elem: etree._Element,
        raw_data: str,
    ) -> SearchResult:
        """Parse MODS formatted record.

        Args:
            record_elem: XML element containing MODS data.
            raw_data: Raw XML string.

        Returns:
            Parsed SearchResult.
        """
        result = SearchResult(raw_data=raw_data, format=RecordFormat.MODS)

        # Extract title
        title_elem = record_elem.find(
            ".//mods:titleInfo/mods:title",
            namespaces=self.NAMESPACES,
        )
        if title_elem is not None:
            result.title = title_elem.text

        # Extract author
        author_elem = record_elem.find(
            ".//mods:name[@type='personal']/mods:namePart",
            namespaces=self.NAMESPACES,
        )
        if author_elem is not None:
            result.author = author_elem.text

        # Extract year
        year_elem = record_elem.find(
            ".//mods:originInfo/mods:dateIssued",
            namespaces=self.NAMESPACES,
        )
        if year_elem is not None:
            result.year = year_elem.text

        # Extract publisher
        publisher_elem = record_elem.find(
            ".//mods:originInfo/mods:publisher",
            namespaces=self.NAMESPACES,
        )
        if publisher_elem is not None:
            result.publisher = publisher_elem.text

        # Extract ISBN
        isbn_elem = record_elem.find(
            ".//mods:identifier[@type='isbn']",
            namespaces=self.NAMESPACES,
        )
        if isbn_elem is not None:
            result.isbn = isbn_elem.text

        return result

    def close(self) -> None:
        """Close the session and release resources."""
        self.session.close()

    def __enter__(self) -> "SWBClient":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self.close()
