"""Tests for input validation in the SRU API client."""

import pytest

from swb.api import SWBClient
from swb.exceptions import ValidationError
from swb.models import RelationType


@pytest.fixture
def client() -> SWBClient:
    """Create a test client instance."""
    return SWBClient()


class TestSearchValidation:
    """Tests for search() method input validation."""

    def test_search_empty_query_raises_error(self, client: SWBClient) -> None:
        """Test that empty query raises ValueError."""
        with pytest.raises(ValidationError, match="Query cannot be empty"):
            client.search("")

    def test_search_whitespace_query_raises_error(self, client: SWBClient) -> None:
        """Test that whitespace-only query raises ValueError."""
        with pytest.raises(ValidationError, match="Query cannot be empty"):
            client.search("   ")

    def test_search_start_record_zero_raises_error(self, client: SWBClient) -> None:
        """Test that start_record=0 raises ValueError."""
        with pytest.raises(ValidationError, match="start_record must be >= 1, got 0"):
            client.search("test", start_record=0)

    def test_search_start_record_negative_raises_error(self, client: SWBClient) -> None:
        """Test that negative start_record raises ValueError."""
        with pytest.raises(ValidationError, match="start_record must be >= 1, got -1"):
            client.search("test", start_record=-1)

    def test_search_maximum_records_zero_raises_error(self, client: SWBClient) -> None:
        """Test that maximum_records=0 raises ValueError."""
        with pytest.raises(ValidationError, match="maximum_records must be >= 1, got 0"):
            client.search("test", maximum_records=0)

    def test_search_maximum_records_negative_raises_error(
        self, client: SWBClient
    ) -> None:
        """Test that negative maximum_records raises ValueError."""
        with pytest.raises(ValidationError, match="maximum_records must be >= 1, got -5"):
            client.search("test", maximum_records=-5)

    def test_search_maximum_records_over_100_logs_warning(
        self, client: SWBClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that maximum_records > 100 logs a warning."""
        from unittest.mock import Mock, patch

        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
            <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
                <numberOfRecords>0</numberOfRecords>
            </searchRetrieveResponse>"""
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # Should not raise but should warn
            client.search("test", maximum_records=150)

            # Check that warning was logged
            assert "maximum_records=150 may be rejected by server" in caplog.text
            assert "Most SRU servers limit to 100 records per request" in caplog.text


class TestSearchByISBNValidation:
    """Tests for search_by_isbn() method input validation."""

    def test_search_by_isbn_empty_raises_error(self, client: SWBClient) -> None:
        """Test that empty ISBN raises ValueError."""
        with pytest.raises(ValidationError, match="ISBN cannot be empty"):
            client.search_by_isbn("")

    def test_search_by_isbn_whitespace_raises_error(self, client: SWBClient) -> None:
        """Test that whitespace-only ISBN raises ValueError."""
        with pytest.raises(ValidationError, match="ISBN cannot be empty"):
            client.search_by_isbn("   ")

    def test_search_by_isbn_only_separators_raises_error(
        self, client: SWBClient
    ) -> None:
        """Test that ISBN with only separators raises ValueError."""
        with pytest.raises(
            ValidationError, match="ISBN cannot be empty after removing separators"
        ):
            client.search_by_isbn("---")

    def test_search_by_isbn_only_spaces_raises_error(self, client: SWBClient) -> None:
        """Test that ISBN with only spaces raises ValidationError."""
        with pytest.raises(
            ValidationError, match="ISBN cannot be empty"
        ):
            client.search_by_isbn("   ")


class TestSearchByISSNValidation:
    """Tests for search_by_issn() method input validation."""

    def test_search_by_issn_empty_raises_error(self, client: SWBClient) -> None:
        """Test that empty ISSN raises ValueError."""
        with pytest.raises(ValidationError, match="ISSN cannot be empty"):
            client.search_by_issn("")

    def test_search_by_issn_whitespace_raises_error(self, client: SWBClient) -> None:
        """Test that whitespace-only ISSN raises ValueError."""
        with pytest.raises(ValidationError, match="ISSN cannot be empty"):
            client.search_by_issn("   ")

    def test_search_by_issn_only_separators_raises_error(
        self, client: SWBClient
    ) -> None:
        """Test that ISSN with only separators or spaces raises ValidationError."""
        with pytest.raises(
            ValidationError, match="ISSN cannot be empty after removing separators"
        ):
            client.search_by_issn("---")

    def test_search_by_issn_only_spaces_raises_error(self, client: SWBClient) -> None:
        """Test that ISSN with only separators or spaces raises ValidationError."""
        with pytest.raises(
            ValidationError, match="ISSN cannot be empty"
        ):
            client.search_by_issn("   ")


class TestScanValidation:
    """Tests for scan() method input validation."""

    def test_scan_empty_clause_raises_error(self, client: SWBClient) -> None:
        """Test that empty scan_clause raises ValueError."""
        with pytest.raises(ValidationError, match="scan_clause cannot be empty"):
            client.scan("")

    def test_scan_whitespace_clause_raises_error(self, client: SWBClient) -> None:
        """Test that whitespace-only scan_clause raises ValueError."""
        with pytest.raises(ValidationError, match="scan_clause cannot be empty"):
            client.scan("   ")

    def test_scan_response_position_zero_raises_error(
        self, client: SWBClient
    ) -> None:
        """Test that response_position=0 raises ValueError."""
        with pytest.raises(ValidationError, match="response_position must be >= 1, got 0"):
            client.scan("pica.per=Test", response_position=0)

    def test_scan_response_position_negative_raises_error(
        self, client: SWBClient
    ) -> None:
        """Test that negative response_position raises ValueError."""
        with pytest.raises(ValidationError, match="response_position must be >= 1, got -1"):
            client.scan("pica.per=Test", response_position=-1)

    def test_scan_maximum_terms_zero_raises_error(self, client: SWBClient) -> None:
        """Test that maximum_terms=0 raises ValueError."""
        with pytest.raises(ValidationError, match="maximum_terms must be >= 1, got 0"):
            client.scan("pica.per=Test", maximum_terms=0)

    def test_scan_maximum_terms_negative_raises_error(
        self, client: SWBClient
    ) -> None:
        """Test that negative maximum_terms raises ValueError."""
        with pytest.raises(ValidationError, match="maximum_terms must be >= 1, got -3"):
            client.scan("pica.per=Test", maximum_terms=-3)


class TestSearchRelatedValidation:
    """Tests for search_related() method input validation."""

    def test_search_related_empty_ppn_raises_error(self, client: SWBClient) -> None:
        """Test that empty ppn raises ValueError."""
        with pytest.raises(ValidationError, match="ppn cannot be empty"):
            client.search_related("", RelationType.CHILD)

    def test_search_related_whitespace_ppn_raises_error(
        self, client: SWBClient
    ) -> None:
        """Test that whitespace-only ppn raises ValueError."""
        with pytest.raises(ValidationError, match="ppn cannot be empty"):
            client.search_related("   ", RelationType.CHILD)

    def test_search_related_start_record_zero_raises_error(
        self, client: SWBClient
    ) -> None:
        """Test that start_record=0 raises ValueError."""
        with pytest.raises(ValidationError, match="start_record must be >= 1, got 0"):
            client.search_related("123456", RelationType.CHILD, start_record=0)

    def test_search_related_start_record_negative_raises_error(
        self, client: SWBClient
    ) -> None:
        """Test that negative start_record raises ValueError."""
        with pytest.raises(ValidationError, match="start_record must be >= 1, got -2"):
            client.search_related("123456", RelationType.CHILD, start_record=-2)

    def test_search_related_maximum_records_zero_raises_error(
        self, client: SWBClient
    ) -> None:
        """Test that maximum_records=0 raises ValueError."""
        with pytest.raises(ValidationError, match="maximum_records must be >= 1, got 0"):
            client.search_related("123456", RelationType.CHILD, maximum_records=0)

    def test_search_related_maximum_records_negative_raises_error(
        self, client: SWBClient
    ) -> None:
        """Test that negative maximum_records raises ValueError."""
        with pytest.raises(ValidationError, match="maximum_records must be >= 1, got -4"):
            client.search_related("123456", RelationType.CHILD, maximum_records=-4)
