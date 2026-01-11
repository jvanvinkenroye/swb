"""Integration tests for the SRU API client.

These tests make actual API calls to the SWB/K10plus servers.
They are marked with @pytest.mark.integration and can be skipped with:
    pytest -m "not integration"

Run only integration tests with:
    pytest -m integration
"""

import pytest

from swb.api import SWBClient
from swb.models import RecordFormat, RelationType, SearchIndex


@pytest.mark.integration
@pytest.mark.slow
class TestRealAPISearch:
    """Integration tests for search() method."""

    def test_real_search_basic_query(self) -> None:
        """Test actual search with basic query."""
        with SWBClient() as client:
            response = client.search("Python programming", maximum_records=1)

            # Should get some results
            assert response.total_results > 0
            assert len(response.results) > 0

            # Results should have basic fields
            result = response.results[0]
            assert result.record_id is not None

    def test_real_search_with_isbn(self) -> None:
        """Test search by ISBN with real API."""
        with SWBClient() as client:
            # Use a well-known ISBN (this is a real book: "The Pragmatic Programmer")
            response = client.search_by_isbn("978-0-13-595705-9", maximum_records=1)

            # May or may not find results, but should not error
            assert response is not None
            assert isinstance(response.total_results, int)

    def test_real_search_with_title_index(self) -> None:
        """Test search with specific title index."""
        with SWBClient() as client:
            response = client.search(
                "Introduction to Algorithms",
                index=SearchIndex.TITLE,
                maximum_records=2,
            )

            # Should find some results
            assert response.total_results >= 0
            assert isinstance(response.results, list)

    def test_real_search_with_author_index(self) -> None:
        """Test search with author index."""
        with SWBClient() as client:
            response = client.search(
                "Knuth", index=SearchIndex.AUTHOR, maximum_records=2
            )

            # Should find Donald Knuth's works
            assert response.total_results > 0
            assert len(response.results) > 0

    def test_real_search_with_subject(self) -> None:
        """Test search with subject index."""
        with SWBClient() as client:
            response = client.search(
                "Computer Science",
                index=SearchIndex.SUBJECT,
                maximum_records=2,
            )

            assert response.total_results >= 0

    def test_real_search_marcxml_format(self) -> None:
        """Test search with MARCXML format (default)."""
        with SWBClient() as client:
            response = client.search(
                "Python", record_format=RecordFormat.MARCXML, maximum_records=1
            )

            assert response.total_results >= 0

    def test_real_search_turbomarc_format(self) -> None:
        """Test search with TurboMARC format."""
        with SWBClient() as client:
            response = client.search(
                "Python", record_format=RecordFormat.TURBOMARC, maximum_records=1
            )

            assert response.total_results >= 0


@pytest.mark.integration
@pytest.mark.slow
class TestRealAPIScan:
    """Integration tests for scan() method."""

    def test_real_scan_title_index(self) -> None:
        """Test actual scan operation on title index."""
        with SWBClient() as client:
            response = client.scan(
                scan_clause="Python", index=SearchIndex.TITLE, maximum_terms=5
            )

            # Should get some scan terms
            assert len(response.terms) > 0
            assert response.terms[0].value is not None
            assert response.terms[0].number_of_records >= 0

    def test_real_scan_author_index(self) -> None:
        """Test scan operation on author index."""
        with SWBClient() as client:
            response = client.scan(
                scan_clause="Smith", index=SearchIndex.AUTHOR, maximum_terms=5
            )

            assert len(response.terms) > 0


@pytest.mark.integration
class TestRealAPIExplain:
    """Integration tests for explain() method."""

    def test_real_explain_operation(self) -> None:
        """Test actual explain operation."""
        with SWBClient() as client:
            response = client.explain()

            # Should get server information
            assert response.server_info is not None
            assert response.server_info.host is not None
            assert response.database_info is not None

    def test_real_explain_has_indices(self) -> None:
        """Test that explain returns available indices."""
        with SWBClient() as client:
            response = client.explain()

            # Should have index information
            assert len(response.indices) > 0
            # Should include common indices like title, author
            index_names = {idx.name.lower() for idx in response.indices}
            assert any("title" in name for name in index_names)


@pytest.mark.integration
class TestRealAPISearchRelated:
    """Integration tests for search_related() method."""

    @pytest.mark.skip(reason="Requires a known PPN with related records")
    def test_real_search_related_child_records(self) -> None:
        """Test searching for related child records.

        Note: This test is skipped because we need a specific PPN
        that is known to have child records. In a real scenario,
        you would use a PPN from a multi-volume work.
        """
        with SWBClient() as client:
            # Example PPN (would need to be a real one with child records)
            response = client.search_related(
                ppn="123456789", relation_type=RelationType.CHILD, maximum_records=5
            )

            assert response is not None


@pytest.mark.integration
class TestRealAPIHoldings:
    """Integration tests for holdings information."""

    def test_real_search_with_holdings(self) -> None:
        """Test search with holdings information."""
        with SWBClient() as client:
            response = client.search("Python programming", maximum_records=1)

            # Should get results
            assert response.total_results > 0

            # Check if holdings information is available
            if len(response.results) > 0:
                result = response.results[0]
                # Holdings may or may not be present depending on the record
                assert isinstance(result.holdings, list)


@pytest.mark.integration
class TestRealAPIDifferentProfiles:
    """Integration tests for different library profiles."""

    def test_k10plus_profile(self) -> None:
        """Test search using K10plus endpoint."""
        client = SWBClient(base_url="https://sru.k10plus.de/k10plus")
        with client:
            response = client.search("Python", maximum_records=1)
            assert response is not None

    @pytest.mark.skip(reason="DNB may have different access requirements")
    def test_dnb_profile(self) -> None:
        """Test search using DNB endpoint.

        Note: The Deutsche Nationalbibliothek may have different
        access requirements or rate limits.
        """
        client = SWBClient(base_url="https://services.dnb.de/sru/dnb")
        with client:
            response = client.search("Python", maximum_records=1)
            assert response is not None


@pytest.mark.integration
@pytest.mark.slow
class TestRealAPIPerformance:
    """Integration tests for API performance."""

    def test_search_response_time_reasonable(self) -> None:
        """Test that search completes in reasonable time."""
        import time

        with SWBClient() as client:
            start_time = time.time()
            response = client.search("test", maximum_records=1)
            elapsed_time = time.time() - start_time

            # Should complete within 10 seconds
            assert elapsed_time < 10.0
            assert response is not None

    def test_multiple_sequential_searches(self) -> None:
        """Test multiple sequential searches (connection reuse)."""
        with SWBClient() as client:
            # Should reuse connection via session
            for query in ["Python", "Java", "Ruby"]:
                response = client.search(query, maximum_records=1)
                assert response is not None


@pytest.mark.integration
class TestRealAPIErrorHandling:
    """Integration tests for error handling with real API."""

    def test_search_with_invalid_query_graceful_handling(self) -> None:
        """Test that server handles unusual queries gracefully."""
        with SWBClient() as client:
            # Search with special characters
            response = client.search("!@#$%^&*()", maximum_records=1)

            # Should not crash, may return 0 results
            assert response is not None
            assert response.total_results >= 0

    def test_search_with_very_long_query(self) -> None:
        """Test handling of very long query string."""
        with SWBClient() as client:
            # Very long query
            long_query = "Python " * 100

            # Should either work or fail gracefully
            try:
                response = client.search(long_query, maximum_records=1)
                assert response is not None
            except Exception as e:
                # If it fails, it should fail with a reasonable error
                assert isinstance(e, (ValueError, requests.RequestException))
