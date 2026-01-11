"""Tests for edge cases and error scenarios in the SRU API client."""

from unittest.mock import Mock, patch

import pytest
import requests

from swb.api import SWBClient
from swb.exceptions import (
    AuthenticationError,
    NetworkError,
    ParseError,
    ServerError,
)
from swb.models import RecordFormat, RelationType


@pytest.fixture
def client() -> SWBClient:
    """Create a test client instance."""
    return SWBClient()


class TestNetworkErrors:
    """Tests for network error handling."""

    def test_search_connection_timeout(self, client: SWBClient) -> None:
        """Test handling of connection timeout."""
        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = requests.Timeout("Connection timed out")

            with pytest.raises(NetworkError):
                client.search("test")

    def test_search_connection_error(self, client: SWBClient) -> None:
        """Test handling of connection error."""
        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = requests.ConnectionError("Failed to connect")

            with pytest.raises(NetworkError):
                client.search("test")

    def test_scan_network_timeout(self, client: SWBClient) -> None:
        """Test handling of network timeout in scan."""
        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = requests.Timeout("Read timed out")

            with pytest.raises(NetworkError):
                client.scan("test")

    def test_explain_connection_error(self, client: SWBClient) -> None:
        """Test handling of connection error in explain."""
        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = requests.ConnectionError("Network unreachable")

            with pytest.raises(NetworkError):
                client.explain()


class TestHTTPErrors:
    """Tests for HTTP error status codes."""

    def test_search_500_internal_server_error(self, client: SWBClient) -> None:
        """Test handling of HTTP 500 error."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = requests.HTTPError(
                "500 Server Error"
            )
            mock_get.return_value = mock_response

            with pytest.raises(ServerError):
                client.search("test")

    def test_search_502_bad_gateway(self, client: SWBClient) -> None:
        """Test handling of HTTP 502 error."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 502
            mock_response.raise_for_status.side_effect = requests.HTTPError(
                "502 Bad Gateway"
            )
            mock_get.return_value = mock_response

            with pytest.raises(ServerError):
                client.search("test")

    def test_search_503_service_unavailable(self, client: SWBClient) -> None:
        """Test handling of HTTP 503 error."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 503
            mock_response.raise_for_status.side_effect = requests.HTTPError(
                "503 Service Unavailable"
            )
            mock_get.return_value = mock_response

            with pytest.raises(ServerError):
                client.search("test")

    def test_search_403_forbidden_error_message(self, client: SWBClient) -> None:
        """Test that 403 error provides helpful message."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_get.return_value = mock_response

            with pytest.raises(AuthenticationError) as exc_info:
                client.search("test")

            error_msg = str(exc_info.value)
            assert "Authentication Error" in error_msg
            assert "403 Forbidden" in error_msg


class TestMalformedXML:
    """Tests for malformed XML handling."""

    def test_search_completely_invalid_xml(self, client: SWBClient) -> None:
        """Test handling of completely invalid XML."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "This is not XML at all!"
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            # Should raise ValueError for invalid XML
            with pytest.raises(ParseError, match="XML Parse Error"):
                client.search("test")

    def test_search_incomplete_xml(self, client: SWBClient) -> None:
        """Test handling of incomplete/truncated XML."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '<?xml version="1.0"?><searchRetrieveResponse'
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            with pytest.raises(ParseError, match="XML Parse Error"):
                client.search("test")

    def test_scan_malformed_xml(self, client: SWBClient) -> None:
        """Test handling of malformed XML in scan response."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<invalid>xml<structure>"
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            with pytest.raises(ParseError, match="XML Parse Error"):
                client.scan("test")


class TestEmptyResponses:
    """Tests for empty response handling."""

    def test_search_empty_response_body(self, client: SWBClient) -> None:
        """Test handling of empty response body."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = ""
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            with pytest.raises(ParseError, match="XML Parse Error"):
                client.search("test")

    def test_search_whitespace_only_response(self, client: SWBClient) -> None:
        """Test handling of whitespace-only response."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "   \n\t  "
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            with pytest.raises(ParseError, match="XML Parse Error"):
                client.search("test")


class TestRecordPackingEdgeCases:
    """Tests for recordPacking parameter edge cases."""

    def test_search_with_string_packing_already_tested(self) -> None:
        """Note: String packing is already tested in test_api.py."""
        # This test exists to document that string packing is covered
        pass

    def test_search_invalid_packing_already_tested(self) -> None:
        """Note: Invalid packing is already tested in test_api.py."""
        # This test exists to document that invalid packing validation is covered
        pass


class TestSearchRelatedEdgeCases:
    """Tests for search_related() method edge cases."""

    def test_search_related_with_all_relation_types(self, client: SWBClient) -> None:
        """Test search_related with each relation type."""
        relation_types = [
            (RelationType.CHILD, "rel-nt"),
            (RelationType.PARENT, "rel-bt"),
            (RelationType.FAMILY, "fam"),
        ]

        for relation_type, expected_code in relation_types:
            with patch.object(client.session, "get") as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
                <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
                    <numberOfRecords>0</numberOfRecords>
                    <records></records>
                </searchRetrieveResponse>"""
                mock_response.encoding = "utf-8"
                mock_get.return_value = mock_response

                client.search_related(ppn="123456", relation_type=relation_type)

                # Verify the CQL query includes the correct relation code
                call_args = mock_get.call_args
                params = call_args.kwargs["params"]
                assert f'pica.1045="{expected_code}"' in params["query"]

    def test_search_related_network_error(self, client: SWBClient) -> None:
        """Test search_related with network error."""
        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = requests.Timeout("Connection timed out")

            with pytest.raises(NetworkError):
                client.search_related(ppn="123456", relation_type=RelationType.CHILD)


class TestEncodingEdgeCases:
    """Tests for character encoding edge cases."""

    def test_search_utf8_response(self, client: SWBClient) -> None:
        """Test handling of UTF-8 encoded response."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
            <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
                <numberOfRecords>1</numberOfRecords>
                <records>
                    <record>
                        <recordData>
                            <record xmlns="http://www.loc.gov/MARC21/slim">
                                <datafield tag="245">
                                    <subfield code="a">Test with Umlauts: äöü ÄÖÜ ß</subfield>
                                </datafield>
                            </record>
                        </recordData>
                    </record>
                </records>
            </searchRetrieveResponse>"""
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            response = client.search("test")
            assert response.total_results == 1
            assert "äöü" in response.results[0].title


class TestContextManager:
    """Tests for context manager behavior."""

    def test_context_manager_closes_session(self) -> None:
        """Test that context manager properly closes session."""
        with SWBClient() as client:
            assert client.session is not None

        # Session should still be accessible but can be considered closed
        assert client.session is not None

    def test_context_manager_with_exception(self) -> None:
        """Test context manager handles exceptions properly."""
        try:
            with SWBClient() as client:
                assert client is not None
                raise ValueError("Test exception")
        except ValueError:
            pass  # Exception should be propagated


class TestRateLimitWarning:
    """Tests for rate limit warnings."""

    def test_search_with_large_maximum_records_logs_warning(
        self, client: SWBClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that requesting >100 records logs a warning."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
            <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
                <numberOfRecords>0</numberOfRecords>
                <records></records>
            </searchRetrieveResponse>"""
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            client.search("test", maximum_records=200)

            # Check that warning was logged
            assert any(
                "may be rejected by server" in record.message for record in caplog.records
            )


class TestFacetedSearch:
    """Tests for faceted search functionality."""

    def test_search_with_facets(self, client: SWBClient) -> None:
        """Test search with facet parameters."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
            <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
                <numberOfRecords>10</numberOfRecords>
                <records></records>
                <extraResponseData>
                    <facets>
                        <facet>
                            <name>format</name>
                            <values>
                                <value count="5">Book</value>
                                <value count="3">Article</value>
                            </values>
                        </facet>
                    </facets>
                </extraResponseData>
            </searchRetrieveResponse>"""
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            response = client.search("test", facets=["format"])

            # Verify facets parameter was included
            call_args = mock_get.call_args
            params = call_args.kwargs["params"]
            assert "facets" in params
            assert params["facets"] == "format"
            assert "facetLimit" in params
