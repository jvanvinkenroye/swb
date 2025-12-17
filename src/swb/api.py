"""SRU API client for the Südwestdeutscher Bibliotheksverbund (SWB)."""

import logging
from types import TracebackType

import requests
from lxml import etree

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

    def scan(
        self,
        scan_clause: str,
        response_position: int = 1,
        maximum_terms: int = 20,
    ) -> ScanResponse:
        """Scan an index for terms (for auto-completion and browsing).

        The scan operation allows browsing index terms, which is useful for:
        - Auto-completion in search interfaces
        - Exploring available terms before searching
        - Finding correct spellings

        Args:
            scan_clause: CQL scan clause (e.g., "pica.per=Goe" to find authors
                        starting with "Goe").
            response_position: Position in the term list to start from (1-based).
            maximum_terms: Maximum number of terms to return.

        Returns:
            ScanResponse containing the list of terms.

        Raises:
            requests.RequestException: If the API request fails.
            ValueError: If the response cannot be parsed.

        Example:
            >>> client = SWBClient()
            >>> response = client.scan("pica.per=Goe", maximum_terms=10)
            >>> for term in response.terms:
            ...     print(f"{term.value}: {term.number_of_records} records")
        """
        params: dict[str, str | int] = {
            "version": self.SRU_VERSION,
            "operation": "scan",
            "scanClause": scan_clause,
            "responsePosition": response_position,
            "maximumTerms": maximum_terms,
        }

        logger.info(f"Scanning index: {scan_clause}")
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
            logger.error(f"Scan request failed: {e}")
            raise

        return self._parse_scan_response(response.text, scan_clause, response_position)

    def explain(self) -> ExplainResponse:
        """Retrieve server capabilities and configuration (SRU explain operation).

        The explain operation returns information about the server including:
        - Server and database information
        - Available search indices
        - Supported record schemas/formats
        - Configuration details

        Returns:
            ExplainResponse containing server capabilities.

        Raises:
            requests.RequestException: If the API request fails.
            ValueError: If the response cannot be parsed.

        Example:
            >>> client = SWBClient()
            >>> info = client.explain()
            >>> print(f"Database: {info.database_info.title}")
            >>> print(f"Available indices: {len(info.indices)}")
            >>> for schema in info.schemas:
            ...     print(f"  - {schema.name}")
        """
        params = {
            "version": self.SRU_VERSION,
            "operation": "explain",
        }

        logger.info("Fetching server explain record")
        logger.debug(f"Request parameters: {params}")

        try:
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            # Ensure UTF-8 encoding
            response.encoding = "utf-8"
        except requests.RequestException as e:
            logger.error(f"Explain request failed: {e}")
            raise

        return self._parse_explain_response(response.text)

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
        elif record_format == RecordFormat.TURBOMARC:
            return self._parse_turbomarc(record_data_elem, raw_data)
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

    def _parse_turbomarc(
        self,
        record_elem: etree._Element,
        raw_data: str,
    ) -> SearchResult:
        """Parse TurboMARC formatted record.

        TurboMARC is an XML encoding of MARC records optimized for XSLT processing.
        It uses element names instead of attributes for field tags and subfield codes.

        Format:
        - Namespace: http://www.indexdata.com/turbomarc
        - Record element: <r>
        - Control fields: <c001>, <c008>, etc.
        - Data fields: <d245>, <d100>, etc. with i1, i2 attributes
        - Subfields: <sa>, <sb>, <sc>, etc.

        Args:
            record_elem: XML element containing TurboMARC data.
            raw_data: Raw XML string.

        Returns:
            Parsed SearchResult.
        """
        # TurboMARC namespace
        turbomarc_ns = {"tm": "http://www.indexdata.com/turbomarc"}

        result = SearchResult(raw_data=raw_data, format=RecordFormat.TURBOMARC)

        # Extract record ID (control field 001)
        controlfield_001 = record_elem.find(".//tm:c001", namespaces=turbomarc_ns)
        if controlfield_001 is not None and controlfield_001.text:
            result.record_id = controlfield_001.text

        # Extract title (field 245 subfield a)
        title_field = record_elem.find(".//tm:d245/tm:sa", namespaces=turbomarc_ns)
        if title_field is not None and title_field.text:
            result.title = title_field.text

        # Extract author (field 100 or 700 subfield a)
        author_field = record_elem.find(".//tm:d100/tm:sa", namespaces=turbomarc_ns)
        if author_field is None:
            author_field = record_elem.find(".//tm:d700/tm:sa", namespaces=turbomarc_ns)
        if author_field is not None and author_field.text:
            result.author = author_field.text

        # Extract publication year (field 264 or 260 subfield c)
        year_field = record_elem.find(".//tm:d264/tm:sc", namespaces=turbomarc_ns)
        if year_field is None:
            year_field = record_elem.find(".//tm:d260/tm:sc", namespaces=turbomarc_ns)
        if year_field is not None and year_field.text:
            result.year = year_field.text

        # Extract publisher (field 264 or 260 subfield b)
        publisher_field = record_elem.find(".//tm:d264/tm:sb", namespaces=turbomarc_ns)
        if publisher_field is None:
            publisher_field = record_elem.find(
                ".//tm:d260/tm:sb", namespaces=turbomarc_ns
            )
        if publisher_field is not None and publisher_field.text:
            result.publisher = publisher_field.text

        # Extract ISBN (field 020 subfield a)
        isbn_field = record_elem.find(".//tm:d020/tm:sa", namespaces=turbomarc_ns)
        if isbn_field is not None and isbn_field.text:
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

    def _parse_scan_response(
        self,
        xml_data: str,
        scan_clause: str,
        response_position: int,
    ) -> ScanResponse:
        """Parse the SRU scan response.

        Args:
            xml_data: Raw XML response from the scan API.
            scan_clause: Original scan clause.
            response_position: Position in the term list.

        Returns:
            Parsed ScanResponse object.

        Raises:
            ValueError: If the XML cannot be parsed or is invalid.
        """
        try:
            # Encode string to UTF-8 bytes for lxml parsing
            xml_bytes = (
                xml_data.encode("utf-8") if isinstance(xml_data, str) else xml_data
            )
            root = etree.fromstring(xml_bytes)
        except etree.XMLSyntaxError as e:
            logger.error(f"Failed to parse scan XML response: {e}")
            raise ValueError(f"Invalid scan XML response: {e}") from e

        # Parse scan terms
        # The scan response uses a different namespace structure
        ns = {"srw": "http://www.loc.gov/zing/srw/"}
        diag_ns = {
            "srw": "http://www.loc.gov/zing/srw/",
            "diag": "http://www.loc.gov/zing/srw/diagnostic/",
        }

        # Check for diagnostic errors first
        diagnostic = root.find(".//srw:diagnostics/diag:diagnostic", namespaces=diag_ns)
        if diagnostic is not None:
            uri_elem = diagnostic.find("diag:uri", namespaces=diag_ns)
            message_elem = diagnostic.find("diag:message", namespaces=diag_ns)
            error_uri = uri_elem.text if uri_elem is not None else "unknown"
            error_message = (
                message_elem.text if message_elem is not None else "Unknown error"
            )
            raise ValueError(f"SRU scan error ({error_uri}): {error_message}")

        terms = []
        term_elements = root.findall(".//srw:term", namespaces=ns)

        for term_elem in term_elements:
            # Extract term value
            value_elem = term_elem.find("srw:value", namespaces=ns)
            if value_elem is None or value_elem.text is None:
                continue

            # Extract number of records
            num_records_elem = term_elem.find("srw:numberOfRecords", namespaces=ns)
            num_records = (
                int(num_records_elem.text) if num_records_elem is not None else 0
            )

            # Extract display term (optional)
            display_elem = term_elem.find("srw:displayTerm", namespaces=ns)
            display_term = display_elem.text if display_elem is not None else None

            # Extract extra data (optional)
            extra_elem = term_elem.find("srw:extraTermData", namespaces=ns)
            extra_data = extra_elem.text if extra_elem is not None else None

            terms.append(
                ScanTerm(
                    value=value_elem.text,
                    number_of_records=num_records,
                    display_term=display_term,
                    extra_data=extra_data,
                )
            )

        logger.info(f"Parsed {len(terms)} terms from scan response")

        return ScanResponse(
            terms=terms,
            scan_clause=scan_clause,
            response_position=response_position,
        )

    def _parse_explain_response(self, xml_data: str) -> ExplainResponse:
        """Parse the SRU explain response.

        Args:
            xml_data: Raw XML response from the explain API.

        Returns:
            Parsed ExplainResponse object.

        Raises:
            ValueError: If the XML cannot be parsed or is invalid.
        """
        try:
            # Encode string to UTF-8 bytes for lxml parsing
            xml_bytes = (
                xml_data.encode("utf-8") if isinstance(xml_data, str) else xml_data
            )
            root = etree.fromstring(xml_bytes)
        except etree.XMLSyntaxError as e:
            logger.error(f"Failed to parse explain XML response: {e}")
            raise ValueError(f"Invalid explain XML response: {e}") from e

        # Namespaces for explain response
        # Note: Support both 2.0 and 2.1 versions of the explain schema
        ns_list = [
            {
                "zs": "http://www.loc.gov/zing/srw/",
                "zr": "http://explain.z3950.org/dtd/2.0/",
            },
            {
                "zs": "http://www.loc.gov/zing/srw/",
                "zr": "http://explain.z3950.org/dtd/2.1/",
            },
        ]

        # Try to find elements with either namespace version
        ns = ns_list[0]
        for namespace in ns_list:
            if root.find(".//zr:serverInfo", namespaces=namespace) is not None:
                ns = namespace
                break

        # Parse server info
        server_elem = root.find(".//zr:serverInfo", namespaces=ns)
        if server_elem is not None:
            host_elem = server_elem.find(".//zr:host", namespaces=ns)
            port_elem = server_elem.find(".//zr:port", namespaces=ns)
            database_elem = server_elem.find(".//zr:database", namespaces=ns)

            server_info = ServerInfo(
                host=host_elem.text if host_elem is not None else "unknown",
                port=int(port_elem.text) if port_elem is not None and port_elem.text else None,
                database=database_elem.text if database_elem is not None else None,
            )
        else:
            server_info = ServerInfo(host="unknown")

        # Parse database info
        database_elem = root.find(".//zr:databaseInfo", namespaces=ns)
        if database_elem is not None:
            title_elem = database_elem.find(".//zr:title", namespaces=ns)
            description_elem = database_elem.find(".//zr:description", namespaces=ns)
            contact_elem = database_elem.find(".//zr:contact", namespaces=ns)

            database_info = DatabaseInfo(
                title=title_elem.text if title_elem is not None and title_elem.text else "Unknown",
                description=description_elem.text if description_elem is not None else None,
                contact=contact_elem.text if contact_elem is not None else None,
            )
        else:
            database_info = DatabaseInfo(title="Unknown")

        # Parse index info
        indices: list[IndexInfo] = []
        index_elements = root.findall(".//zr:indexInfo/zr:index", namespaces=ns)
        for index_elem in index_elements:
            title_elem = index_elem.find(".//zr:title", namespaces=ns)
            # The map element contains the index name and set
            map_name_elem = index_elem.find(".//zr:map/zr:name", namespaces=ns)

            if title_elem is not None and map_name_elem is not None:
                # Construct full CQL name: set.name (e.g., "pica.tit")
                set_attr = map_name_elem.get("set", "")
                name_text = map_name_elem.text or ""
                full_name = f"{set_attr}.{name_text}" if set_attr else name_text

                indices.append(
                    IndexInfo(
                        title=title_elem.text or "Unknown",
                        name=full_name,
                        description=None,
                    )
                )

        # Parse schema info
        schemas: list[SchemaInfo] = []
        schema_elements = root.findall(".//zr:schemaInfo/zr:schema", namespaces=ns)
        for schema_elem in schema_elements:
            identifier_attr = schema_elem.get("identifier", "")
            name_attr = schema_elem.get("name", "")
            title_elem = schema_elem.find(".//zr:title", namespaces=ns)

            # Use name as identifier if identifier is empty
            schema_id = identifier_attr if identifier_attr else name_attr

            if schema_id:
                schemas.append(
                    SchemaInfo(
                        identifier=schema_id,
                        name=name_attr if name_attr else schema_id,
                        title=title_elem.text if title_elem is not None else None,
                    )
                )

        logger.info(
            f"Parsed explain response: {len(indices)} indices, {len(schemas)} schemas"
        )

        return ExplainResponse(
            server_info=server_info,
            database_info=database_info,
            indices=indices,
            schemas=schemas,
        )

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
