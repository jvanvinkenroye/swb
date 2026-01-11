"""Tests for the SRU API client."""

from unittest.mock import Mock, patch

import pytest
import requests

from swb.api import SWBClient
from swb.models import RecordFormat, RecordType, RelationType, SearchIndex


@pytest.fixture
def client() -> SWBClient:
    """Create a test client instance."""
    return SWBClient()


def test_client_initialization() -> None:
    """Test client initialization with defaults."""
    client = SWBClient()
    assert client.base_url == SWBClient.DEFAULT_BASE_URL
    assert client.timeout == 30


def test_client_custom_url() -> None:
    """Test client initialization with custom URL."""
    custom_url = "https://example.com/sru"
    client = SWBClient(base_url=custom_url)
    assert client.base_url == custom_url


def test_client_context_manager() -> None:
    """Test client as context manager."""
    with SWBClient() as client:
        assert isinstance(client, SWBClient)
        assert client.session is not None


def test_search_query_building(client: SWBClient) -> None:
    """Test CQL query building with search index."""
    with patch.object(client.session, "get") as mock_get:
        # Create a mock response
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>0</numberOfRecords>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Test simple search with index
        client.search("Python", index=SearchIndex.TITLE)

        # Verify the query parameter
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert params["query"] == 'pica.tit="Python"'


def test_search_isbn_cleaning(client: SWBClient) -> None:
    """Test ISBN number cleaning."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>0</numberOfRecords>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Search with formatted ISBN
        client.search_by_isbn("978-3-16-148410-0")

        # Verify hyphens were removed
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert "9783161484100" in params["query"]


def test_search_error_handling(client: SWBClient) -> None:
    """Test error handling for failed requests."""
    with patch.object(client.session, "get") as mock_get:
        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(requests.RequestException):
            client.search("test query")


def test_parse_invalid_xml(client: SWBClient) -> None:
    """Test handling of invalid XML responses."""
    with pytest.raises(ValueError, match="Invalid XML response"):
        client._parse_response("not valid xml", "query", RecordFormat.MARCXML)


def test_parse_empty_response(client: SWBClient) -> None:
    """Test parsing response with no results."""
    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>0</numberOfRecords>
    </searchRetrieveResponse>"""

    response = client._parse_response(xml_response, "test query", RecordFormat.MARCXML)

    assert response.total_results == 0
    assert len(response.results) == 0
    assert response.next_record is None


def test_parse_marcxml_record(client: SWBClient) -> None:
    """Test parsing a MARCXML record."""
    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <controlfield tag="001">123456</controlfield>
                        <datafield tag="245" ind1="1" ind2="0">
                            <subfield code="a">Test Title</subfield>
                        </datafield>
                        <datafield tag="100" ind1="1" ind2=" ">
                            <subfield code="a">Test Author</subfield>
                        </datafield>
                        <datafield tag="264" ind1=" " ind2="1">
                            <subfield code="c">2023</subfield>
                            <subfield code="b">Test Publisher</subfield>
                        </datafield>
                        <datafield tag="020" ind1=" " ind2=" ">
                            <subfield code="a">978-3-16-148410-0</subfield>
                        </datafield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    response = client._parse_response(xml_response, "test query", RecordFormat.MARCXML)

    assert response.total_results == 1
    assert len(response.results) == 1

    result = response.results[0]
    assert result.record_id == "123456"
    assert result.title == "Test Title"
    assert result.author == "Test Author"
    assert result.year == "2023"
    assert result.publisher == "Test Publisher"
    assert result.isbn == "978-3-16-148410-0"


def test_parse_marcxml_with_umlauts(client: SWBClient) -> None:
    """Test parsing MARCXML with German umlauts (UTF-8 encoding)."""
    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <controlfield tag="001">789012</controlfield>
                        <datafield tag="245" ind1="1" ind2="0">
                            <subfield code="a">Einführung in GitHub Copilot</subfield>
                        </datafield>
                        <datafield tag="100" ind1="1" ind2=" ">
                            <subfield code="a">Schürmann, Tim</subfield>
                        </datafield>
                        <datafield tag="264" ind1=" " ind2="1">
                            <subfield code="c">2026</subfield>
                            <subfield code="b">O'Reilly Verlag</subfield>
                        </datafield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    response = client._parse_response(xml_response, "test query", RecordFormat.MARCXML)

    assert response.total_results == 1
    assert len(response.results) == 1

    result = response.results[0]
    # Test that German umlauts are correctly preserved
    assert result.title == "Einführung in GitHub Copilot"
    assert result.author == "Schürmann, Tim"
    assert result.publisher == "O'Reilly Verlag"
    assert result.year == "2026"


def test_parse_turbomarc_record(client: SWBClient) -> None:
    """Test parsing a TurboMARC record."""
    from swb.models import RecordFormat

    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <r xmlns="http://www.indexdata.com/turbomarc">
                        <c001>123456789</c001>
                        <d245 i1="1" i2="0">
                            <sa>Python Programming</sa>
                            <sb>A Comprehensive Guide</sb>
                        </d245>
                        <d100 i1="1" i2=" ">
                            <sa>Doe, John</sa>
                        </d100>
                        <d264 i1=" " i2="1">
                            <sc>2023</sc>
                            <sb>Tech Publishers</sb>
                        </d264>
                        <d020 i1=" " i2=" ">
                            <sa>978-1-234-56789-0</sa>
                        </d020>
                    </r>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    response = client._parse_response(
        xml_response, "test query", RecordFormat.TURBOMARC
    )

    assert response.total_results == 1
    assert len(response.results) == 1

    result = response.results[0]
    assert result.record_id == "123456789"
    assert result.title == "Python Programming"
    assert result.author == "Doe, John"
    assert result.year == "2023"
    assert result.publisher == "Tech Publishers"
    assert result.isbn == "978-1-234-56789-0"
    assert result.format == RecordFormat.TURBOMARC


def test_parse_turbomarc_with_umlauts(client: SWBClient) -> None:
    """Test parsing TurboMARC with German umlauts (UTF-8 encoding)."""
    from swb.models import RecordFormat

    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <r xmlns="http://www.indexdata.com/turbomarc">
                        <c001>987654321</c001>
                        <d245 i1="1" i2="0">
                            <sa>Einführung in GitHub Copilot</sa>
                        </d245>
                        <d100 i1="1" i2=" ">
                            <sa>Schürmann, Tim</sa>
                        </d100>
                        <d264 i1=" " i2="1">
                            <sc>2026</sc>
                            <sb>O'Reilly Verlag</sb>
                        </d264>
                    </r>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    response = client._parse_response(
        xml_response, "test query", RecordFormat.TURBOMARC
    )

    assert response.total_results == 1
    assert len(response.results) == 1

    result = response.results[0]
    # Test that German umlauts are correctly preserved in TurboMARC
    assert result.title == "Einführung in GitHub Copilot"
    assert result.author == "Schürmann, Tim"
    assert result.publisher == "O'Reilly Verlag"
    assert result.year == "2026"


def test_search_with_sorting(client: SWBClient) -> None:
    """Test search with sorting parameters."""
    from swb.models import SortBy, SortOrder

    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>0</numberOfRecords>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_response.encoding = "utf-8"
        mock_get.return_value = mock_response

        # Test sorting by year descending
        client.search(
            "Python",
            sort_by=SortBy.YEAR,
            sort_order=SortOrder.DESCENDING,
        )

        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert "sortKeys" in params
        assert params["sortKeys"] == "year,,0"  # 0 = descending

        # Test sorting by year ascending
        client.search(
            "Python",
            sort_by=SortBy.YEAR,
            sort_order=SortOrder.ASCENDING,
        )

        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert params["sortKeys"] == "year,,1"  # 1 = ascending

        # Test sorting by author
        client.search(
            "Python",
            sort_by=SortBy.AUTHOR,
            sort_order=SortOrder.DESCENDING,
        )

        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert params["sortKeys"] == "author,,0"


def test_search_without_sorting(client: SWBClient) -> None:
    """Test that sortKeys is not added when sorting is not specified."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>0</numberOfRecords>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_response.encoding = "utf-8"
        mock_get.return_value = mock_response

        client.search("Python")

        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert "sortKeys" not in params


def test_scan_operation(client: SWBClient) -> None:
    """Test scan operation for browsing terms."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <scanResponse xmlns="http://www.loc.gov/zing/srw/">
            <terms>
                <term>
                    <value>Goethe, Johann Wolfgang von</value>
                    <numberOfRecords>28531</numberOfRecords>
                    <displayTerm>Goethe, Johann Wolfgang von</displayTerm>
                </term>
                <term>
                    <value>Goebbels, Joseph</value>
                    <numberOfRecords>45</numberOfRecords>
                </term>
                <term>
                    <value>Goebel, Klaus</value>
                    <numberOfRecords>12</numberOfRecords>
                </term>
            </terms>
        </scanResponse>"""
        mock_response.raise_for_status = Mock()
        mock_response.encoding = "utf-8"
        mock_get.return_value = mock_response

        response = client.scan("pica.per=Goe", maximum_terms=10)

        # Verify request parameters
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert params["operation"] == "scan"
        assert params["scanClause"] == "pica.per=Goe"
        assert params["maximumTerms"] == 10

        # Verify response parsing
        assert len(response.terms) == 3
        assert response.scan_clause == "pica.per=Goe"

        # Check first term
        first_term = response.terms[0]
        assert first_term.value == "Goethe, Johann Wolfgang von"
        assert first_term.number_of_records == 28531
        assert first_term.display_term == "Goethe, Johann Wolfgang von"

        # Check second term
        second_term = response.terms[1]
        assert second_term.value == "Goebbels, Joseph"
        assert second_term.number_of_records == 45


def test_scan_empty_response(client: SWBClient) -> None:
    """Test scan with no results."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <scanResponse xmlns="http://www.loc.gov/zing/srw/">
            <terms>
            </terms>
        </scanResponse>"""
        mock_response.raise_for_status = Mock()
        mock_response.encoding = "utf-8"
        mock_get.return_value = mock_response

        response = client.scan("pica.per=ZZZZZ")

        assert len(response.terms) == 0


def test_scan_with_umlauts(client: SWBClient) -> None:
    """Test scan operation with German umlauts."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <scanResponse xmlns="http://www.loc.gov/zing/srw/">
            <terms>
                <term>
                    <value>Schürmann, Tim</value>
                    <numberOfRecords>15</numberOfRecords>
                </term>
                <term>
                    <value>Müller, Hans</value>
                    <numberOfRecords>234</numberOfRecords>
                </term>
            </terms>
        </scanResponse>"""
        mock_response.raise_for_status = Mock()
        mock_response.encoding = "utf-8"
        mock_get.return_value = mock_response

        response = client.scan("pica.per=Schü")

        assert len(response.terms) == 2
        assert response.terms[0].value == "Schürmann, Tim"
        assert response.terms[1].value == "Müller, Hans"


def test_scan_diagnostic_error(client: SWBClient) -> None:
    """Test scan with diagnostic error response."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <scanResponse xmlns="http://www.loc.gov/zing/srw/">
            <version>1.1</version>
            <diagnostics>
                <diagnostic xmlns="http://www.loc.gov/zing/srw/diagnostic/">
                    <uri>info:srw/diagnostic/1/2</uri>
                    <message>System temporarily unavailable</message>
                </diagnostic>
            </diagnostics>
        </scanResponse>"""
        mock_response.raise_for_status = Mock()
        mock_response.encoding = "utf-8"
        mock_get.return_value = mock_response

        with pytest.raises(
            ValueError, match="SRU scan error.*System temporarily unavailable"
        ):
            client.scan("pica.per=Test")


def test_explain_operation(client: SWBClient) -> None:
    """Test explain operation for server capabilities."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <explainResponse xmlns="http://www.loc.gov/zing/srw/">
            <record>
                <recordData>
                    <explain xmlns="http://explain.z3950.org/dtd/2.1/">
                        <serverInfo>
                            <host>sru.k10plus.de</host>
                            <port>80</port>
                            <database>swb</database>
                        </serverInfo>
                        <databaseInfo>
                            <title>SWB - Online-Katalog</title>
                            <description>Südwestdeutscher Bibliotheksverbund</description>
                            <contact>info@bsz-bw.de</contact>
                        </databaseInfo>
                        <indexInfo>
                            <index>
                                <title>Title</title>
                                <map><name>pica.tit</name></map>
                            </index>
                            <index>
                                <title>Author</title>
                                <map><name>pica.per</name></map>
                            </index>
                        </indexInfo>
                        <schemaInfo>
                            <schema identifier="marcxml" name="MARC21 XML">
                                <title>MARC21 XML</title>
                            </schema>
                            <schema identifier="mods" name="MODS">
                                <title>Metadata Object Description Schema</title>
                            </schema>
                        </schemaInfo>
                    </explain>
                </recordData>
            </record>
        </explainResponse>"""
        mock_response.raise_for_status = Mock()
        mock_response.encoding = "utf-8"
        mock_get.return_value = mock_response

        response = client.explain()

        # Verify request parameters
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert params["operation"] == "explain"

        # Verify server info
        assert response.server_info.host == "sru.k10plus.de"
        assert response.server_info.port == 80
        assert response.server_info.database == "swb"

        # Verify database info
        assert response.database_info.title == "SWB - Online-Katalog"
        assert "Südwestdeutscher" in response.database_info.description
        assert response.database_info.contact == "info@bsz-bw.de"

        # Verify indices
        assert len(response.indices) == 2
        assert response.indices[0].title == "Title"
        assert response.indices[0].name == "pica.tit"
        assert response.indices[1].title == "Author"
        assert response.indices[1].name == "pica.per"

        # Verify schemas
        assert len(response.schemas) == 2
        assert response.schemas[0].identifier == "marcxml"
        assert response.schemas[0].name == "MARC21 XML"
        assert response.schemas[1].identifier == "mods"
        assert response.schemas[1].name == "MODS"


def test_search_related_child_records(client: SWBClient) -> None:
    """Test searching for child records (volumes) of a multi-volume work."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>5</numberOfRecords>
            <records>
                <record>
                    <recordData>
                        <record xmlns="http://www.loc.gov/MARC21/slim">
                            <controlfield tag="001">123456</controlfield>
                            <datafield tag="245" ind1="1" ind2="0">
                                <subfield code="a">Volume 1</subfield>
                            </datafield>
                        </record>
                    </recordData>
                </record>
            </records>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Search for child records
        response = client.search_related(
            ppn="267838395",
            relation_type=RelationType.CHILD,
            record_type=RecordType.BIBLIOGRAPHIC,
        )

        # Verify the query was constructed correctly
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert (
            params["query"]
            == 'pica.1049="267838395" and pica.1045="rel-nt" and pica.1001="b"'
        )
        assert params["operation"] == "searchRetrieve"

        # Verify response
        assert response.total_results == 5
        assert len(response.results) == 1


def test_search_related_parent_record(client: SWBClient) -> None:
    """Test searching for parent record of a volume."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>1</numberOfRecords>
            <records>
                <record>
                    <recordData>
                        <record xmlns="http://www.loc.gov/MARC21/slim">
                            <controlfield tag="001">987654</controlfield>
                            <datafield tag="245" ind1="1" ind2="0">
                                <subfield code="a">Parent Work</subfield>
                            </datafield>
                        </record>
                    </recordData>
                </record>
            </records>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Search for parent record
        response = client.search_related(
            ppn="123456789",
            relation_type=RelationType.PARENT,
        )

        # Verify the query was constructed correctly
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert (
            params["query"]
            == 'pica.1049="123456789" and pica.1045="rel-bt" and pica.1001="b"'
        )

        # Verify response
        assert response.total_results == 1
        assert len(response.results) == 1
        assert response.results[0].title == "Parent Work"


def test_search_related_family(client: SWBClient) -> None:
    """Test searching for entire family of related records."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>10</numberOfRecords>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Search for entire family
        response = client.search_related(
            ppn="267838395",
            relation_type=RelationType.FAMILY,
            maximum_records=20,
        )

        # Verify the query was constructed correctly
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert (
            params["query"]
            == 'pica.1049="267838395" and pica.1045="fam" and pica.1001="b"'
        )
        assert params["maximumRecords"] == 20

        # Verify response
        assert response.total_results == 10


def test_search_related_authority_records(client: SWBClient) -> None:
    """Test searching for related authority records."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>3</numberOfRecords>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Search for related authority records
        response = client.search_related(
            ppn="111222333",
            relation_type=RelationType.RELATED,
            record_type=RecordType.AUTHORITY,
        )

        # Verify the query was constructed correctly
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert (
            params["query"]
            == 'pica.1049="111222333" and pica.1045="rel-rt" and pica.1001="n"'
        )

        # Verify response
        assert response.total_results == 3


def test_search_related_with_format(client: SWBClient) -> None:
    """Test searching related records with specific format."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>2</numberOfRecords>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Search with MODS format
        response = client.search_related(
            ppn="444555666",
            relation_type=RelationType.THESAURUS,
            record_format=RecordFormat.MODS,
        )

        # Verify the query and format
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert (
            params["query"]
            == 'pica.1049="444555666" and pica.1045="rel-tt" and pica.1001="b"'
        )
        assert params["recordSchema"] == "mods"

        # Verify response
        assert response.total_results == 2
        assert response.format == RecordFormat.MODS


def test_search_with_xml_packing(client: SWBClient) -> None:
    """Test search with XML record packing (default)."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>1</numberOfRecords>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Search with default (xml) packing
        _ = client.search("Python")

        # Verify recordPacking parameter
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert params["recordPacking"] == "xml"


def test_search_with_string_packing(client: SWBClient) -> None:
    """Test search with string record packing."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>1</numberOfRecords>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Search with string packing
        _ = client.search("Python", record_packing="string")

        # Verify recordPacking parameter
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert params["recordPacking"] == "string"


def test_search_with_invalid_packing(client: SWBClient) -> None:
    """Test search with invalid record packing raises ValueError."""
    with pytest.raises(ValueError, match="Invalid recordPacking value"):
        client.search("Python", record_packing="invalid")


def test_search_by_isbn_with_packing(client: SWBClient) -> None:
    """Test ISBN search supports record packing."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>1</numberOfRecords>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Search with string packing
        _ = client.search_by_isbn("978-3-16-148410-0", record_packing="string")

        # Verify recordPacking parameter
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert params["recordPacking"] == "string"


def test_search_related_with_packing(client: SWBClient) -> None:
    """Test related search supports record packing."""
    with patch.object(client.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
            <numberOfRecords>1</numberOfRecords>
        </searchRetrieveResponse>"""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Search with string packing
        _ = client.search_related(
            ppn="123456", relation_type=RelationType.CHILD, record_packing="string"
        )

        # Verify recordPacking parameter
        call_args = mock_get.call_args
        assert call_args is not None
        params = call_args.kwargs["params"]
        assert params["recordPacking"] == "string"


def test_parse_marcxml_legacy_record(client: SWBClient) -> None:
    """Test parsing a MARCXML Legacy record (uses same parser as MARCXML)."""
    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <controlfield tag="001">654321</controlfield>
                        <datafield tag="245" ind1="1" ind2="0">
                            <subfield code="a">Legacy Title</subfield>
                        </datafield>
                        <datafield tag="100" ind1="1" ind2=" ">
                            <subfield code="a">Legacy Author</subfield>
                        </datafield>
                        <datafield tag="264" ind1=" " ind2="1">
                            <subfield code="c">2020</subfield>
                        </datafield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    response = client._parse_response(
        xml_response, "test query", RecordFormat.MARCXML_LEGACY
    )

    assert response.total_results == 1
    assert len(response.results) == 1

    result = response.results[0]
    assert result.record_id == "654321"
    assert result.title == "Legacy Title"
    assert result.author == "Legacy Author"
    assert result.year == "2020"
    assert result.format == RecordFormat.MARCXML_LEGACY


def test_parse_mods36_record(client: SWBClient) -> None:
    """Test parsing a MODS 3.6 record (uses same parser as MODS)."""
    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <mods xmlns="http://www.loc.gov/mods/v3">
                        <titleInfo>
                            <title>MODS 3.6 Title</title>
                        </titleInfo>
                        <name type="personal">
                            <namePart>MODS 3.6 Author</namePart>
                        </name>
                        <originInfo>
                            <dateIssued>2021</dateIssued>
                        </originInfo>
                    </mods>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    response = client._parse_response(xml_response, "test query", RecordFormat.MODS36)

    assert response.total_results == 1
    assert len(response.results) == 1

    result = response.results[0]
    assert result.title == "MODS 3.6 Title"
    assert result.author == "MODS 3.6 Author"
    assert result.year == "2021"
    assert result.format == RecordFormat.MODS36


def test_parse_mads_record(client: SWBClient) -> None:
    """Test parsing a MADS record (returns raw data only)."""
    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <mads xmlns="http://www.loc.gov/mads/v2">
                        <authority>
                            <name type="personal">
                                <namePart>Test Authority</namePart>
                            </name>
                        </authority>
                    </mads>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    response = client._parse_response(xml_response, "test query", RecordFormat.MADS)

    assert response.total_results == 1
    assert len(response.results) == 1

    result = response.results[0]
    # MADS format returns raw data without parsing specific fields
    assert result.raw_data is not None
    assert "mads" in result.raw_data.lower()
    assert result.format == RecordFormat.MADS


def test_parse_holdings(client: SWBClient) -> None:
    """Test parsing library holdings from MARC field 924."""
    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <controlfield tag="001">123456789</controlfield>
                        <datafield tag="245" ind1="0" ind2="0">
                            <subfield code="a">Test Title</subfield>
                        </datafield>
                        <datafield tag="924" ind1="1" ind2=" ">
                            <subfield code="b">DE-21</subfield>
                            <subfield code="k">https://example.com/access</subfield>
                            <subfield code="l">Campus access only</subfield>
                            <subfield code="g">E-Book Collection</subfield>
                        </datafield>
                        <datafield tag="924" ind1="1" ind2=" ">
                            <subfield code="b">DE-15</subfield>
                            <subfield code="k">https://example.com/rostock</subfield>
                            <subfield code="l">Online access</subfield>
                        </datafield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    response = client._parse_response(xml_response, "test query", RecordFormat.MARCXML)

    assert response.total_results == 1
    assert len(response.results) == 1

    result = response.results[0]
    assert result.title == "Test Title"
    assert len(result.holdings) == 2

    # Check first holding
    holding1 = result.holdings[0]
    assert holding1.library_code == "DE-21"
    assert holding1.library_name == "Universität Stuttgart"
    assert holding1.access_url == "https://example.com/access"
    assert holding1.access_note == "Campus access only"
    assert holding1.collection == "E-Book Collection"

    # Check second holding
    holding2 = result.holdings[1]
    assert holding2.library_code == "DE-15"
    assert holding2.library_name == "Universitätsbibliothek Rostock"
    assert holding2.access_url == "https://example.com/rostock"
    assert holding2.access_note == "Online access"
    assert holding2.collection is None


def test_parse_holdings_multiple_access_notes(client: SWBClient) -> None:
    """Test parsing holdings with multiple access notes."""
    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <controlfield tag="001">123456789</controlfield>
                        <datafield tag="245" ind1="0" ind2="0">
                            <subfield code="a">Test Title</subfield>
                        </datafield>
                        <datafield tag="924" ind1="1" ind2=" ">
                            <subfield code="b">DE-Lg1</subfield>
                            <subfield code="l">Online access</subfield>
                            <subfield code="l">VPN required</subfield>
                            <subfield code="l">Campus network only</subfield>
                        </datafield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    response = client._parse_response(xml_response, "test query", RecordFormat.MARCXML)

    result = response.results[0]
    assert len(result.holdings) == 1

    holding = result.holdings[0]
    assert holding.library_code == "DE-Lg1"
    assert holding.access_note == "Online access / VPN required / Campus network only"


def test_parse_holdings_unknown_library(client: SWBClient) -> None:
    """Test parsing holdings for unknown library code."""
    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <controlfield tag="001">123456789</controlfield>
                        <datafield tag="245" ind1="0" ind2="0">
                            <subfield code="a">Test Title</subfield>
                        </datafield>
                        <datafield tag="924" ind1="1" ind2=" ">
                            <subfield code="b">DE-UNKNOWN</subfield>
                        </datafield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    response = client._parse_response(xml_response, "test query", RecordFormat.MARCXML)

    result = response.results[0]
    assert len(result.holdings) == 1

    holding = result.holdings[0]
    assert holding.library_code == "DE-UNKNOWN"
    # Should generate a fallback name when not in mapping
    assert holding.library_name == "German Library (DE-UNKNOWN)"


def test_parse_holdings_no_holdings(client: SWBClient) -> None:
    """Test parsing record without holdings."""
    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <controlfield tag="001">123456789</controlfield>
                        <datafield tag="245" ind1="0" ind2="0">
                            <subfield code="a">Test Title</subfield>
                        </datafield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    response = client._parse_response(xml_response, "test query", RecordFormat.MARCXML)

    result = response.results[0]
    assert len(result.holdings) == 0


def test_xxe_attack_prevention_in_search(client: SWBClient) -> None:
    """Test that XXE attacks are prevented in search response parsing."""
    # XXE attack payload that tries to read a file
    xxe_payload = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE foo [
        <!ENTITY xxe SYSTEM "file:///nonexistent/test/file">
    ]>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <controlfield tag="001">&xxe;</controlfield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    # This should parse successfully but entities should NOT be resolved
    response = client._parse_response(xxe_payload, "test query", RecordFormat.MARCXML)

    # Verify the entity was NOT expanded (should be empty or None, not file contents)
    result = response.results[0]
    # The secure parser should not resolve the entity, so record_id should be None or empty
    assert result.record_id is None or result.record_id == ""


def test_xxe_attack_prevention_in_scan(client: SWBClient) -> None:
    """Test that XXE attacks are prevented in scan response parsing."""
    # XXE attack payload in scan response
    xxe_payload = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE foo [
        <!ENTITY xxe SYSTEM "file:///nonexistent/test/file">
    ]>
    <scanResponse xmlns="http://www.loc.gov/zing/srw/">
        <terms>
            <term>
                <value>&xxe;</value>
                <numberOfRecords>1</numberOfRecords>
            </term>
        </terms>
    </scanResponse>"""

    # This should parse successfully but entities should NOT be resolved
    response = client._parse_scan_response(xxe_payload, "test scan", 1)

    # Verify the entity was NOT expanded
    # When entity is not resolved, value_elem.text is None and the term is skipped
    # This is the correct security behavior - no data should be exposed
    assert len(response.terms) == 0


def test_xxe_attack_prevention_in_explain(client: SWBClient) -> None:
    """Test that XXE attacks are prevented in explain response parsing."""
    # XXE attack payload in explain response
    xxe_payload = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE foo [
        <!ENTITY xxe SYSTEM "file:///nonexistent/test/file">
    ]>
    <explainResponse xmlns="http://www.loc.gov/zing/srw/">
        <record>
            <recordData>
                <explain xmlns="http://explain.z3950.org/dtd/2.0/">
                    <serverInfo>
                        <host>&xxe;</host>
                        <port>80</port>
                        <database>testdb</database>
                    </serverInfo>
                    <databaseInfo>
                        <title>Test Database</title>
                    </databaseInfo>
                </explain>
            </recordData>
        </record>
    </explainResponse>"""

    # This should parse successfully but entities should NOT be resolved
    response = client._parse_explain_response(xxe_payload)

    # Verify the entity was NOT expanded
    # The secure parser should not resolve the entity
    assert response.server_info.host == "" or response.server_info.host is None


def test_billion_laughs_attack_prevention(client: SWBClient) -> None:
    """Test that billion laughs (entity expansion DoS) attacks are prevented."""
    # Billion laughs attack payload (simplified version)
    billion_laughs_payload = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE foo [
        <!ENTITY lol "lol">
        <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
        <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
        <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
    ]>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <controlfield tag="001">&lol3;</controlfield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    # This should parse successfully without expanding entities to massive size
    response = client._parse_response(
        billion_laughs_payload, "test query", RecordFormat.MARCXML
    )

    # Verify the entity was NOT expanded (should be empty or None)
    result = response.results[0]
    assert result.record_id is None or result.record_id == ""


def test_external_dtd_attack_prevention(client: SWBClient) -> None:
    """Test that external DTD attacks are prevented."""
    # External DTD attack payload using a reserved test domain
    external_dtd_payload = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE foo SYSTEM "http://evil.test/evil.dtd">
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>0</numberOfRecords>
    </searchRetrieveResponse>"""

    # This should parse successfully but NOT fetch the external DTD
    # The no_network=True setting prevents network access
    response = client._parse_response(
        external_dtd_payload, "test query", RecordFormat.MARCXML
    )

    # Should successfully parse without network access
    assert response.total_results == 0
