"""Tests for data models."""

from swb.models import (
    LibraryHolding,
    RecordFormat,
    SearchIndex,
    SearchResponse,
    SearchResult,
)


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
    assert result.holdings == []  # Should be initialized to empty list


def test_search_result_holdings_initialization() -> None:
    """Test SearchResult holdings field is properly initialized."""
    # Test default initialization creates empty list
    result1 = SearchResult()
    assert result1.holdings == []
    assert isinstance(result1.holdings, list)

    # Test that each instance gets its own list (no shared mutable default)
    result2 = SearchResult()
    result1.holdings.append(LibraryHolding(library_code="DE-21"))
    assert len(result1.holdings) == 1
    assert len(result2.holdings) == 0  # Should not be affected

    # Test explicit None is converted to empty list
    result3 = SearchResult(holdings=None)
    assert result3.holdings == []

    # Test explicit list is preserved
    holdings_list = [LibraryHolding(library_code="DE-15")]
    result4 = SearchResult(holdings=holdings_list)
    assert result4.holdings == holdings_list
    assert len(result4.holdings) == 1


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
