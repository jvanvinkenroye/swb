"""Tests for data models."""

from swb.models import RecordFormat, SearchIndex, SearchResponse, SearchResult


def test_record_format_enum() -> None:
    """Test RecordFormat enum values."""
    assert RecordFormat.MARCXML.value == "marcxml"
    assert RecordFormat.MODS.value == "mods"
    assert RecordFormat.PICA.value == "picaxml"
    assert RecordFormat.DUBLIN_CORE.value == "dc"


def test_search_index_enum() -> None:
    """Test SearchIndex enum values."""
    assert SearchIndex.TITLE.value == "pica.tit"
    assert SearchIndex.AUTHOR.value == "pica.per"
    assert SearchIndex.ISBN.value == "pica.isb"


def test_search_result_defaults() -> None:
    """Test SearchResult default values."""
    result = SearchResult()
    assert result.record_id is None
    assert result.title is None
    assert result.author is None
    assert result.year is None
    assert result.publisher is None
    assert result.isbn is None
    assert result.format == RecordFormat.MARCXML


def test_search_result_with_data() -> None:
    """Test SearchResult with data."""
    result = SearchResult(
        record_id="123456",
        title="Test Book",
        author="Test Author",
        year="2023",
        isbn="978-3-16-148410-0",
    )
    assert result.record_id == "123456"
    assert result.title == "Test Book"
    assert result.author == "Test Author"
    assert result.year == "2023"
    assert result.isbn == "978-3-16-148410-0"


def test_search_response_has_more() -> None:
    """Test SearchResponse has_more property."""
    # No more results
    response = SearchResponse(
        total_results=5,
        results=[],
        next_record=None,
    )
    assert not response.has_more

    # Has more results
    response = SearchResponse(
        total_results=100,
        results=[],
        next_record=11,
    )
    assert response.has_more

    # Next record exceeds total
    response = SearchResponse(
        total_results=10,
        results=[],
        next_record=15,
    )
    assert not response.has_more
