"""SRU API client for the Südwestdeutscher Bibliotheksverbund (SWB)."""

import logging
from types import TracebackType

import requests
from lxml import etree

from swb.models import (
    DatabaseInfo,
    ExplainResponse,
    Facet,
    FacetValue,
    IndexInfo,
    LibraryHolding,
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

    # Library code to name mapping (commonly seen in SWB and other German library networks)
    LIBRARY_NAMES = {
        # Major universities
        "DE-1": "Universität Tübingen",
        "DE-14": "Universität Konstanz",
        "DE-15": "Universitätsbibliothek Rostock",
        "DE-16": "Universität Freiburg",
        "DE-21": "Universität Stuttgart",
        "DE-26": "Universität Hohenheim",
        "DE-28": "Universität Ulm",
        "DE-29": "Universität Heidelberg",
        "DE-705": "Universität Mannheim",
        "DE-31": "Badische Landesbibliothek Karlsruhe",
        # Technical universities
        "DE-Ch1": "TU Chemnitz",
        "DE-289": "Pädagogische Hochschule Karlsruhe",
        "DE-Fn1": "Hochschule Furtwangen",
        "DE-1033": "Hochschule Offenburg",
        "DE-Mh35": "Hochschule Mannheim",
        "DE-943": "Hochschule für Technik Stuttgart",
        "DE-Ofb1": "Hochschule Biberach",
        "DE-16-300": "Universitätsbibliothek Freiburg (Sondersammlung)",
        "DE-14-1": "Universität Konstanz (Fachbereich 1)",
        "DE-14-2": "Universität Konstanz (Fachbereich 2)",
        # Pedagogical universities
        "DE-Frei129": "Pädagogische Hochschule Freiburg",
        "DE-Lg1": "Pädagogische Hochschule Ludwigsburg",
        "DE-747": "Hochschule Ravensburg-Weingarten",
        "DE-Frei26": "PH Freiburg",
        "DE-Zi4": "Pädagogische Hochschule Schwäbisch Gmünd",
        "DE-953": "PH Weingarten",
        "DE-Frei160": "Evangelische Hochschule Freiburg",
        "DE-944": "HfWU Nürtingen-Geislingen",
        "DE-753": "Hochschule Aalen",
        "DE-576": "Hochschule Esslingen",
        "DE-840": "Duale Hochschule Baden-Württemberg (DHBW) Stuttgart",
        "DE-Loer2": "Hochschule für Forstwirtschaft Rottenburg",
        # Other important institutions
        "DE-752": "Kommunikations- und Informationszentrum Ulm",
        "DE-751": "Thüringer Universitäts- und Landesbibliothek Jena",
        # Additional common libraries
        "DE-2": "Universität Hohenheim",
        "DE-3": "Universität Stuttgart (Zentralbibliothek)",
        "DE-4": "Universität Tübingen (Theologische Fakultät)",
        "DE-5": "Universität Tübingen (Medizinische Fakultät)",
        "DE-6": "Universität Tübingen (Juristische Fakultät)",
        "DE-7": "Universität Tübingen (Wirtschafts- und Sozialwissenschaftliche Fakultät)",
        "DE-8": "Universität Tübingen (Philosophische Fakultät)",
        "DE-9": "Universität Tübingen (Mathematisch-Naturwissenschaftliche Fakultät)",
        "DE-10": "Universität Konstanz (Hauptbibliothek)",
        "DE-11": "Universität Konstanz (Fachbereichsbibliothek)",
        "DE-12": "Universität Freiburg (Universitätsbibliothek)",
        "DE-13": "Universität Freiburg (Fachbibliotheken)",
        "DE-17": "Universität Heidelberg",
        "DE-18": "Universität Heidelberg (Medizinische Fakultät)",
        "DE-19": "Universität Heidelberg (Juristische Fakultät)",
        "DE-20": "Universität Heidelberg (Philosophische Fakultät)",
        "DE-22": "Universität Stuttgart (Fachbibliotheken)",
        "DE-23": "Universität Stuttgart (Technische Fakultät)",
        "DE-24": "Universität Stuttgart (Architektur und Stadtplanung)",
        "DE-25": "Universität Stuttgart (Bau- und Umweltingenieurwissenschaften)",
        "DE-27": "Universität Ulm (Medizinische Fakultät)",
        "DE-30": "Universität Mannheim (Schlossbibliothek)",
        # State libraries
        "DE-32": "Württembergische Landesbibliothek Stuttgart",
        "DE-33": "Bayerische Staatsbibliothek München",
        "DE-34": "Staatsbibliothek zu Berlin",
        # Special libraries
        "DE-100": "Deutsche Nationalbibliothek Frankfurt",
        "DE-101": "Deutsche Nationalbibliothek Leipzig",
        "DE-200": "Zentralbibliothek Zürich (for Swiss holdings)",
        "DE-300": "Österreichische Nationalbibliothek Wien (for Austrian holdings)",
    }

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = 30,
        api_key: str | None = None,
    ) -> None:
        """Initialize the SWB API client.

        Args:
            base_url: Custom base URL for the SRU endpoint.
                     Defaults to the official SWB endpoint.
            timeout: Request timeout in seconds. Defaults to 30.
            api_key: Optional API key for authentication if required by the server.
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "SWB-Python-Client/0.1.0 (+https://github.com/yourusername/swb)",
                "Accept": "application/xml",
                "Accept-Encoding": "gzip, deflate",
            }
        )

        # Add API key if provided
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def search(
        self,
        query: str,
        record_format: RecordFormat = RecordFormat.MARCXML,
        start_record: int = 1,
        maximum_records: int = 10,
        index: SearchIndex | None = None,
        sort_by: SortBy | None = None,
        sort_order: SortOrder = SortOrder.DESCENDING,
        record_packing: str = "xml",
        facets: list[str] | None = None,
        facet_limit: int = 10,
        sru_version: str | None = None,
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
            record_packing: How records are packed in the response. Valid values:
                          "xml" (default) - Records embedded as XML
                          "string" - Records escaped as strings
            facets: List of facet fields to request (requires SRU 2.0).
                   Examples: ["year", "author", "subject"]
            facet_limit: Maximum number of facet values per facet field. Default is 10.
            sru_version: SRU version to use. If facets are requested, defaults to "2.0",
                        otherwise uses the client's default version.

        Returns:
            SearchResponse containing the search results and facets (if requested).

        Raises:
            requests.RequestException: If the API request fails.
            ValueError: If the response cannot be parsed or recordPacking is invalid.

        Example:
            >>> client = SWBClient()
            >>> results = client.search(
            ...     "Python",
            ...     index=SearchIndex.TITLE,
            ...     sort_by=SortBy.YEAR,
            ...     sort_order=SortOrder.DESCENDING,
            ...     facets=["year", "author"],
            ...     facet_limit=20
            ... )
            >>> print(f"Found {results.total_results} results")
            >>> if results.facets:
            ...     for facet in results.facets:
            ...         print(f"{facet.name}: {len(facet.values)} values")
        """
        # Validate recordPacking parameter
        if record_packing not in ("xml", "string"):
            raise ValueError(
                f"Invalid recordPacking value: {record_packing}. "
                "Valid values are 'xml' or 'string'."
            )

        # Build CQL query if index is specified
        if index:
            cql_query = f'{index.value}="{query}"'
        else:
            cql_query = query

        # Use SRU 2.0 if facets are requested, unless version is explicitly set
        version = sru_version or ("2.0" if facets else self.SRU_VERSION)

        params = {
            "version": version,
            "operation": "searchRetrieve",
            "query": cql_query,
            "recordSchema": record_format.value,
            "startRecord": start_record,
            "maximumRecords": maximum_records,
            "recordPacking": record_packing,
        }

        # Add sorting if specified
        # sortKeys format: <field>,,<order> where order: 0=descending, 1=ascending
        if sort_by:
            sort_order_value = "1" if sort_order == SortOrder.ASCENDING else "0"
            params["sortKeys"] = f"{sort_by.value},,{sort_order_value}"

        # Add facet parameters if specified (SRU 2.0 feature)
        if facets:
            # SRU 2.0 facet parameter format (may vary by implementation)
            # Common formats: comma-separated list or multiple parameters
            params["facets"] = ",".join(facets)
            params["facetLimit"] = facet_limit

        logger.info(f"Searching SWB: {cql_query}")
        logger.debug(f"Request parameters: {params}")

        try:
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=self.timeout,
            )

            # Handle specific HTTP status codes with helpful messages
            if response.status_code == 403:
                error_msg = f"Access denied (403 Forbidden) from {self.base_url}"
                error_msg += "\nPossible causes:\n"
                error_msg += "- The SRU server may require authentication\n"
                error_msg += "- Your IP address may be blocked\n"
                error_msg += "- The server may have changed its access policy\n"
                error_msg += "\nTry:\n"
                error_msg += (
                    "- Using a different profile (--profile k10plus, dnb, etc.)\n"
                )
                error_msg += "- Checking if the server requires an API key\n"
                error_msg += "- Using a VPN or different network connection\n"
                logger.error(error_msg)
                raise requests.HTTPError(error_msg, response=response)

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
        record_packing: str = "xml",
    ) -> SearchResponse:
        """Search for a book by ISBN.

        Args:
            isbn: ISBN number (with or without hyphens).
            record_format: Desired format for the results.
            record_packing: How records are packed ("xml" or "string"). Default is "xml".

        Returns:
            SearchResponse containing the search results.
        """
        # Remove common ISBN separators
        clean_isbn = isbn.replace("-", "").replace(" ", "")
        return self.search(
            clean_isbn,
            record_format=record_format,
            index=SearchIndex.ISBN,
            record_packing=record_packing,
        )

    def search_by_issn(
        self,
        issn: str,
        record_format: RecordFormat = RecordFormat.MARCXML,
        record_packing: str = "xml",
    ) -> SearchResponse:
        """Search for a periodical by ISSN.

        Args:
            issn: ISSN number (with or without hyphens).
            record_format: Desired format for the results.
            record_packing: How records are packed ("xml" or "string"). Default is "xml".

        Returns:
            SearchResponse containing the search results.
        """
        clean_issn = issn.replace("-", "").replace(" ", "")
        return self.search(
            clean_issn,
            record_format=record_format,
            index=SearchIndex.ISSN,
            record_packing=record_packing,
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

            # Handle specific HTTP status codes with helpful messages
            if response.status_code == 403:
                error_msg = f"Access denied (403 Forbidden) from {self.base_url}"
                error_msg += "\nPossible causes:\n"
                error_msg += "- The SRU server may require authentication\n"
                error_msg += "- Your IP address may be blocked\n"
                error_msg += "- The server may have changed its access policy\n"
                error_msg += "\nTry:\n"
                error_msg += (
                    "- Using a different profile (--profile k10plus, dnb, etc.)\n"
                )
                error_msg += "- Checking if the server requires an API key\n"
                error_msg += "- Using a VPN or different network connection\n"
                logger.error(error_msg)
                raise requests.HTTPError(error_msg, response=response)

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

            # Handle specific HTTP status codes with helpful messages
            if response.status_code == 403:
                error_msg = f"Access denied (403 Forbidden) from {self.base_url}"
                error_msg += "\nPossible causes:\n"
                error_msg += "- The SRU server may require authentication\n"
                error_msg += "- Your IP address may be blocked\n"
                error_msg += "- The server may have changed its access policy\n"
                error_msg += "\nTry:\n"
                error_msg += (
                    "- Using a different profile (--profile k10plus, dnb, etc.)\n"
                )
                error_msg += "- Checking if the server requires an API key\n"
                error_msg += "- Using a VPN or different network connection\n"
                logger.error(error_msg)
                raise requests.HTTPError(error_msg, response=response)

            response.raise_for_status()
            # Ensure UTF-8 encoding
            response.encoding = "utf-8"
        except requests.RequestException as e:
            logger.error(f"Explain request failed: {e}")
            raise

        return self._parse_explain_response(response.text)

    def search_related(
        self,
        ppn: str,
        relation_type: RelationType,
        record_type: RecordType = RecordType.BIBLIOGRAPHIC,
        record_format: RecordFormat = RecordFormat.MARCXML,
        start_record: int = 1,
        maximum_records: int = 10,
        sort_by: SortBy | None = None,
        sort_order: SortOrder = SortOrder.DESCENDING,
        record_packing: str = "xml",
    ) -> SearchResponse:
        """Search for records related to a specific publication (band/linking search).

        This method is useful for finding related publications in multi-volume works,
        series, or hierarchical bibliographic relationships. It uses K10plus-specific
        search attributes to retrieve linked records.

        Args:
            ppn: PPN (PICA Production Number) of the parent record to find related
                records for.
            relation_type: Type of relationship to search for (e.g., parent, child,
                family, related, thesaurus).
            record_type: Type of records to retrieve (bibliographic or authority).
                Default is bibliographic records.
            record_format: Desired format for the results.
            start_record: Position of first record to return (1-based).
            maximum_records: Maximum number of records to return.
            sort_by: Sort results by relevance, year, author, or title.
            sort_order: Sort order (ascending or descending). Default is descending.
            record_packing: How records are packed ("xml" or "string"). Default is "xml".

        Returns:
            SearchResponse containing the related records.

        Raises:
            requests.RequestException: If the API request fails.
            ValueError: If the response cannot be parsed.

        Example:
            >>> client = SWBClient()
            >>> # Find all child records (volumes) of a multi-volume work
            >>> results = client.search_related(
            ...     ppn="267838395",
            ...     relation_type=RelationType.CHILD,
            ...     maximum_records=20
            ... )
            >>> print(f"Found {results.total_results} related records")
        """
        # Construct CQL query using K10plus band search attributes:
        # - pica.1049: Control number (PPN) linking
        # - pica.1045: Relationship type (fam, rel-bt, rel-nt, rel-rt, rel-tt)
        # - pica.1001: Record type (b=bibliographic, n=authority)
        cql_query = (
            f'pica.1049="{ppn}" and '
            f'pica.1045="{relation_type.value}" and '
            f'pica.1001="{record_type.value}"'
        )

        logger.info(
            f"Searching for related records: ppn={ppn}, "
            f"relation={relation_type.value}, type={record_type.value}"
        )

        return self.search(
            query=cql_query,
            record_format=record_format,
            start_record=start_record,
            maximum_records=maximum_records,
            sort_by=sort_by,
            sort_order=sort_order,
            record_packing=record_packing,
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

        # Parse facets if present (SRU 2.0 feature)
        facets = self._parse_facets(root)

        return SearchResponse(
            total_results=total_results,
            results=results,
            next_record=next_record,
            query=query,
            format=record_format,
            facets=facets,
        )

    def _parse_facets(self, root: etree._Element) -> list[Facet] | None:
        """Parse facets from SRU 2.0 response.

        Args:
            root: Root element of the SRU XML response.

        Returns:
            List of Facet objects or None if no facets present.

        Note:
            SRU 2.0 facet format may vary by server implementation.
            This implementation follows the SRU 2.0 specification for facets.
        """
        # Look for facets in the SRU response
        # SRU 2.0 facet format: <srw:facetedResults>
        faceted_results = root.find(".//srw:facetedResults", namespaces=self.NAMESPACES)
        
        if faceted_results is None:
            return None

        facets = []
        
        # Parse each facet field
        facet_fields = faceted_results.findall(".//srw:facet", namespaces=self.NAMESPACES)
        
        for facet_field in facet_fields:
            # Get facet name/index
            facet_index_elem = facet_field.find(".//srw:index", namespaces=self.NAMESPACES)
            if facet_index_elem is None or not facet_index_elem.text:
                continue
                
            facet_name = facet_index_elem.text
            
            # Parse facet terms/values
            facet_values = []
            terms = facet_field.findall(".//srw:term", namespaces=self.NAMESPACES)
            
            for term in terms:
                # Get term value
                term_value_elem = term.find(".//srw:actualTerm", namespaces=self.NAMESPACES)
                if term_value_elem is None or not term_value_elem.text:
                    # Try alternative element name
                    term_value_elem = term.find(".//srw:value", namespaces=self.NAMESPACES)
                    if term_value_elem is None or not term_value_elem.text:
                        continue
                
                term_value = term_value_elem.text
                
                # Get term count
                count_elem = term.find(".//srw:count", namespaces=self.NAMESPACES)
                count = int(count_elem.text) if count_elem is not None and count_elem.text else 0
                
                facet_values.append(FacetValue(value=term_value, count=count))
            
            if facet_values:
                facets.append(Facet(name=facet_name, values=facet_values))
        
        logger.info(f"Parsed {len(facets)} facets from response")
        return facets if facets else None

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

        # Check if record is string-packed (text content) or XML-packed (child elements)
        if len(record_data_elem) == 0 and record_data_elem.text:
            # String-packed record: recordData contains escaped XML as text
            raw_data = record_data_elem.text
            # For string-packed records, just return the raw escaped string
            # Users who need string packing can parse it themselves
            return SearchResult(raw_data=raw_data, format=record_format)

        # XML-packed record: recordData contains XML child elements
        # Convert record data to string
        raw_data = etree.tostring(
            record_data_elem[0],
            encoding="unicode",
            pretty_print=True,
        )

        # Parse based on format
        if record_format == RecordFormat.MARCXML:
            return self._parse_marcxml(record_data_elem, raw_data, record_format)
        elif record_format == RecordFormat.MARCXML_LEGACY:
            # Legacy MARCXML uses same structure as MARCXML
            return self._parse_marcxml(record_data_elem, raw_data, record_format)
        elif record_format == RecordFormat.TURBOMARC:
            return self._parse_turbomarc(record_data_elem, raw_data)
        elif record_format == RecordFormat.MODS:
            return self._parse_mods(record_data_elem, raw_data, record_format)
        elif record_format == RecordFormat.MODS36:
            # MODS 3.6 uses same structure as MODS
            return self._parse_mods(record_data_elem, raw_data, record_format)
        else:
            # For other formats (MADS, etc.), just return raw data
            return SearchResult(raw_data=raw_data, format=record_format)

    def _parse_marcxml(
        self,
        record_elem: etree._Element,
        raw_data: str,
        record_format: RecordFormat = RecordFormat.MARCXML,
    ) -> SearchResult:
        """Parse MARCXML formatted record.

        Args:
            record_elem: XML element containing MARC data.
            raw_data: Raw XML string.
            record_format: Record format to use (MARCXML or MARCXML_LEGACY).

        Returns:
            Parsed SearchResult.
        """
        result = SearchResult(raw_data=raw_data, format=record_format)

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

        # Extract library holdings (MARC 924)
        result.holdings = self._parse_holdings(record_elem)

        return result

    def _parse_holdings(self, record_elem: etree._Element) -> list[LibraryHolding]:
        """Parse library holdings from MARC field 924.

        Field 924 contains local library holdings information including:
        - Library codes
        - Access URLs
        - Access notes/restrictions
        - Collection information

        Args:
            record_elem: XML element containing MARC data.

        Returns:
            List of LibraryHolding objects.
        """
        holdings = []

        # Find all field 924 entries
        holding_fields = record_elem.findall(
            ".//marc:datafield[@tag='924']",
            namespaces=self.NAMESPACES,
        )

        for field in holding_fields:
            # Extract library code (subfield b)
            library_code_elem = field.find(
                "marc:subfield[@code='b']",
                namespaces=self.NAMESPACES,
            )
            if library_code_elem is None or not library_code_elem.text:
                continue

            library_code = library_code_elem.text.strip()

            # Get library name from mapping or use code
            library_name = self.LIBRARY_NAMES.get(library_code, None)
            if not library_name:
                # Try to extract institution type from code pattern
                if library_code.startswith("DE-"):
                    suffix = library_code[3:]
                    if suffix.isdigit():
                        library_name = f"German Library (DE-{suffix})"
                    else:
                        library_name = f"German Library ({library_code})"
                else:
                    library_name = f"Library ({library_code})"

            # Extract access URL (subfield k)
            access_url_elem = field.find(
                "marc:subfield[@code='k']",
                namespaces=self.NAMESPACES,
            )
            access_url = (
                access_url_elem.text.strip()
                if access_url_elem is not None and access_url_elem.text
                else None
            )

            # Extract access notes (subfield l) - can have multiple
            access_notes = []
            access_note_elems = field.findall(
                "marc:subfield[@code='l']",
                namespaces=self.NAMESPACES,
            )
            for note_elem in access_note_elems:
                if note_elem.text:
                    access_notes.append(note_elem.text.strip())
            access_note = " / ".join(access_notes) if access_notes else None

            # Extract collection name (subfield g)
            collection_elem = field.find(
                "marc:subfield[@code='g']",
                namespaces=self.NAMESPACES,
            )
            collection = (
                collection_elem.text.strip()
                if collection_elem is not None and collection_elem.text
                else None
            )

            holding = LibraryHolding(
                library_code=library_code,
                library_name=library_name,
                access_url=access_url,
                access_note=access_note,
                collection=collection,
            )
            holdings.append(holding)

        return holdings

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
        record_format: RecordFormat = RecordFormat.MODS,
    ) -> SearchResult:
        """Parse MODS formatted record.

        Args:
            record_elem: XML element containing MODS data.
            raw_data: Raw XML string.
            record_format: Record format to use (MODS or MODS36).

        Returns:
            Parsed SearchResult.
        """
        result = SearchResult(raw_data=raw_data, format=record_format)

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
                port=int(port_elem.text)
                if port_elem is not None and port_elem.text
                else None,
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
                title=title_elem.text
                if title_elem is not None and title_elem.text
                else "Unknown",
                description=description_elem.text
                if description_elem is not None
                else None,
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
