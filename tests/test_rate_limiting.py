"""Tests for rate limiting functionality."""

import time
from unittest.mock import Mock, patch

import pytest

from swb.api import SWBClient


@pytest.fixture
def mock_search_response() -> str:
    """Create a mock search response."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <controlfield tag="001">123456</controlfield>
                        <datafield tag="245">
                            <subfield code="a">Test Title</subfield>
                        </datafield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_no_rate_limit_by_default(self, mock_search_response: str) -> None:
        """Test that rate limiting is disabled by default."""
        client = SWBClient()
        assert client.rate_limit is None
        assert client._request_times == []

    def test_rate_limit_initialization(self) -> None:
        """Test rate limit initialization."""
        client = SWBClient(rate_limit=5)
        assert client.rate_limit == 5
        assert client._request_times == []

    def test_rate_limiting_enforced(self, mock_search_response: str) -> None:
        """Test that rate limiting is enforced."""
        client = SWBClient(rate_limit=2)  # 2 requests per second

        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_search_response
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            start = time.time()

            # Make 3 requests (should take ~0.5 seconds with 2 req/s limit)
            for i in range(3):
                client.search(f"test{i}")

            elapsed = time.time() - start

            # Should take at least 0.4 seconds (allowing some margin)
            # 3 requests at 2 req/s means 3rd request needs to wait ~0.5s
            assert elapsed >= 0.4

    def test_no_rate_limiting_when_disabled(self, mock_search_response: str) -> None:
        """Test that no rate limiting occurs when disabled."""
        client = SWBClient()  # No rate limit

        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_search_response
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            start = time.time()

            # Make 5 requests quickly
            for i in range(5):
                client.search(f"test{i}")

            elapsed = time.time() - start

            # Should be very fast (< 0.5 seconds)
            assert elapsed < 0.5

    def test_rate_limit_sliding_window(self, mock_search_response: str) -> None:
        """Test that rate limiting uses a sliding window."""
        client = SWBClient(rate_limit=2)

        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_search_response
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            # Make 2 requests (should be fast)
            client.search("test1")
            client.search("test2")
            assert len(client._request_times) == 2

            # Wait a bit, then make another request
            time.sleep(0.3)
            client.search("test3")

            # Should have 3 request times, but old ones will be removed
            # in the next rate limit check
            assert len(client._request_times) == 3

    def test_rate_limit_with_scan(self, mock_search_response: str) -> None:
        """Test that rate limiting works with scan operation."""
        client = SWBClient(rate_limit=2)

        mock_scan_response = """<?xml version="1.0" encoding="UTF-8"?>
        <scanResponse xmlns="http://www.loc.gov/zing/srw/">
            <terms>
                <term>
                    <value>Test</value>
                    <numberOfRecords>10</numberOfRecords>
                </term>
            </terms>
        </scanResponse>"""

        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_scan_response
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            start = time.time()

            # Make 3 scan requests
            for i in range(3):
                client.scan(f"test{i}")

            elapsed = time.time() - start

            # Should enforce rate limiting
            assert elapsed >= 0.4

    def test_rate_limit_with_explain(self) -> None:
        """Test that rate limiting works with explain operation."""
        client = SWBClient(rate_limit=2)

        mock_explain_response = """<?xml version="1.0" encoding="UTF-8"?>
        <explainResponse xmlns="http://www.loc.gov/zing/srw/">
            <record>
                <recordData>
                    <explain xmlns="http://explain.z3950.org/dtd/2.0/">
                        <serverInfo>
                            <host>test.example.com</host>
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

        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_explain_response
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            start = time.time()

            # Make 3 explain requests
            for i in range(3):
                client.explain()

            elapsed = time.time() - start

            # Should enforce rate limiting
            assert elapsed >= 0.4

    def test_rate_limit_different_operations(self, mock_search_response: str) -> None:
        """Test that rate limiting applies across different operations."""
        client = SWBClient(rate_limit=2)

        mock_scan_response = """<?xml version="1.0" encoding="UTF-8"?>
        <scanResponse xmlns="http://www.loc.gov/zing/srw/">
            <terms>
                <term>
                    <value>Test</value>
                    <numberOfRecords>10</numberOfRecords>
                </term>
            </terms>
        </scanResponse>"""

        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200

            def response_side_effect(*args, **kwargs):
                # Return different responses based on operation
                params = kwargs.get("params", {})
                operation = params.get("operation", "searchRetrieve")

                mock = Mock()
                mock.status_code = 200
                mock.encoding = "utf-8"

                if operation == "scan":
                    mock.text = mock_scan_response
                else:
                    mock.text = mock_search_response

                return mock

            mock_get.side_effect = response_side_effect

            start = time.time()

            # Mix of search and scan operations (3 total)
            client.search("test1")
            client.scan("test2")
            client.search("test3")

            elapsed = time.time() - start

            # Should enforce rate limiting across all operations
            assert elapsed >= 0.4

    def test_rate_limit_logging(
        self, mock_search_response: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that rate limiting logs debug messages."""
        import logging

        # Set logging level to DEBUG to capture rate limit messages
        caplog.set_level(logging.DEBUG)

        client = SWBClient(rate_limit=2)

        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_search_response
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            # Make 3 requests to trigger rate limiting
            client.search("test1")
            client.search("test2")
            client.search("test3")  # This should trigger rate limiting

            # Check that rate limiting was logged
            assert any(
                "Rate limit reached" in record.message for record in caplog.records
            )

    def test_high_rate_limit(self, mock_search_response: str) -> None:
        """Test with a higher rate limit."""
        client = SWBClient(rate_limit=10)

        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_search_response
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            start = time.time()

            # Make 5 requests (under the limit)
            for i in range(5):
                client.search(f"test{i}")

            elapsed = time.time() - start

            # Should be fast since we're under the rate limit
            assert elapsed < 1.0

    def test_rate_limit_with_context_manager(self, mock_search_response: str) -> None:
        """Test rate limiting works with context manager."""
        with SWBClient(rate_limit=2) as client:
            with patch.object(client.session, "get") as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = mock_search_response
                mock_response.encoding = "utf-8"
                mock_get.return_value = mock_response

                start = time.time()

                # Make 3 requests
                for i in range(3):
                    client.search(f"test{i}")

                elapsed = time.time() - start

                # Should enforce rate limiting
                assert elapsed >= 0.4
