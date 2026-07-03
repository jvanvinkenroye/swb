"""Tests for the CLI interface."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from swb.cli import cli, handle_api_error, resolve_base_url
from swb.exceptions import (
    AuthenticationError,
    NetworkError,
    ParseError,
    RateLimitError,
    ServerError,
    SWBError,
    ValidationError,
)
from swb.models import (
    Facet,
    FacetValue,
    LibraryHolding,
    RecordFormat,
    SearchResponse,
    SearchResult,
)


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_search_response() -> SearchResponse:
    """Create a mock search response."""
    return SearchResponse(
        total_results=2,
        results=[
            SearchResult(
                record_id="1",
                title="Python Programming",
                author="John Doe",
                year="2023",
                isbn="978-1234567890",
            ),
            SearchResult(
                record_id="2",
                title="Advanced Python",
                author="Jane Smith",
                year="2024",
                isbn="978-0987654321",
            ),
        ],
        query='pica.tit="Python"',
    )


def test_cli_version(runner: CliRunner) -> None:
    """Test --version flag."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_help(runner: CliRunner) -> None:
    """Test --help flag."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "SWB API Client" in result.output


def test_search_command_help(runner: CliRunner) -> None:
    """Test search command help."""
    result = runner.invoke(cli, ["search", "--help"])
    assert result.exit_code == 0
    assert "Search the SWB catalog" in result.output


@patch("swb.cli.SWBClient")
def test_search_command(
    mock_client_class: Mock,
    runner: CliRunner,
    mock_search_response: SearchResponse,
) -> None:
    """Test basic search command."""
    # Setup mock
    mock_client = Mock()
    mock_client.search.return_value = mock_search_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    # Run command
    result = runner.invoke(cli, ["search", "Python"])

    # Verify
    assert result.exit_code == 0
    assert "Python Programming" in result.output
    assert "John Doe" in result.output
    mock_client.search.assert_called_once()


@patch("swb.cli.SWBClient")
def test_search_with_index(
    mock_client_class: Mock,
    runner: CliRunner,
    mock_search_response: SearchResponse,
) -> None:
    """Test search with specific index."""
    mock_client = Mock()
    mock_client.search.return_value = mock_search_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(cli, ["search", "Python", "--index", "title"])

    assert result.exit_code == 0
    mock_client.search.assert_called_once()


@patch("swb.cli.SWBClient")
def test_isbn_command(
    mock_client_class: Mock,
    runner: CliRunner,
    mock_search_response: SearchResponse,
) -> None:
    """Test ISBN search command."""
    mock_client = Mock()
    mock_client.search_by_isbn.return_value = mock_search_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(cli, ["isbn", "978-3-16-148410-0"])

    assert result.exit_code == 0
    mock_client.search_by_isbn.assert_called_once_with(
        "978-3-16-148410-0", record_format=RecordFormat.MARCXML, record_packing="xml"
    )


@patch("swb.cli.SWBClient")
def test_issn_command(
    mock_client_class: Mock,
    runner: CliRunner,
    mock_search_response: SearchResponse,
) -> None:
    """Test ISSN search command."""
    mock_client = Mock()
    mock_client.search_by_issn.return_value = mock_search_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(cli, ["issn", "0028-0836"])

    assert result.exit_code == 0
    mock_client.search_by_issn.assert_called_once_with(
        "0028-0836", record_format=RecordFormat.MARCXML, record_packing="xml"
    )


def test_formats_command(runner: CliRunner) -> None:
    """Test formats list command."""
    result = runner.invoke(cli, ["formats"])
    assert result.exit_code == 0
    assert "MARCXML" in result.output
    assert "MODS" in result.output


def test_indices_command(runner: CliRunner) -> None:
    """Test indices list command."""
    result = runner.invoke(cli, ["indices"])
    assert result.exit_code == 0
    assert "TITLE" in result.output
    assert "AUTHOR" in result.output


@patch("swb.cli.SWBClient")
def test_search_no_results(
    mock_client_class: Mock,
    runner: CliRunner,
) -> None:
    """Test search with no results."""
    mock_client = Mock()
    mock_client.search.return_value = SearchResponse(
        total_results=0, results=[], query="nonexistent"
    )
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(cli, ["search", "nonexistent"])

    assert result.exit_code == 0
    assert "No results found" in result.output


@patch("swb.cli.SWBClient")
def test_search_quiet_mode(
    mock_client_class: Mock,
    runner: CliRunner,
    mock_search_response: SearchResponse,
) -> None:
    """Test search in quiet mode."""
    mock_client = Mock()
    mock_client.search.return_value = mock_search_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(cli, ["--quiet", "search", "Python"])

    assert result.exit_code == 0
    # Should not contain search summary in quiet mode
    assert "Searching for:" not in result.output


@patch("swb.cli.SWBClient")
def test_search_with_sorting(
    mock_client_class: Mock,
    runner: CliRunner,
    mock_search_response: SearchResponse,
) -> None:
    """Test search with sorting options."""
    from swb.models import SortBy, SortOrder

    mock_client = Mock()
    mock_client.search.return_value = mock_search_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        cli, ["search", "Python", "--sort-by", "year", "--sort-order", "descending"]
    )

    assert result.exit_code == 0
    assert "Sort: YEAR (DESCENDING)" in result.output

    # Verify the client was called with correct sorting parameters
    call_args = mock_client.search.call_args
    assert call_args is not None
    assert call_args.kwargs["sort_by"] == SortBy.YEAR
    assert call_args.kwargs["sort_order"] == SortOrder.DESCENDING


@patch("swb.cli.SWBClient")
def test_search_with_sorting_ascending(
    mock_client_class: Mock,
    runner: CliRunner,
    mock_search_response: SearchResponse,
) -> None:
    """Test search with ascending sort order."""
    from swb.models import SortBy, SortOrder

    mock_client = Mock()
    mock_client.search.return_value = mock_search_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        cli, ["search", "Python", "--sort-by", "author", "--sort-order", "ascending"]
    )

    assert result.exit_code == 0
    call_args = mock_client.search.call_args
    assert call_args is not None
    assert call_args.kwargs["sort_by"] == SortBy.AUTHOR
    assert call_args.kwargs["sort_order"] == SortOrder.ASCENDING


@patch("swb.cli.SWBClient")
def test_scan_command(mock_client_class: Mock, runner: CliRunner) -> None:
    """Test scan command."""
    from swb.models import ScanResponse, ScanTerm

    mock_scan_response = ScanResponse(
        terms=[
            ScanTerm(value="Goethe, Johann Wolfgang von", number_of_records=28531),
            ScanTerm(value="Goebbels, Joseph", number_of_records=45),
            ScanTerm(value="Goebel, Klaus", number_of_records=12),
        ],
        scan_clause="pica.per=Goe",
    )

    mock_client = Mock()
    mock_client.scan.return_value = mock_scan_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(cli, ["scan", "pica.per=Goe"])

    assert result.exit_code == 0
    assert "Goethe, Johann Wolfgang von" in result.output
    assert "28531" in result.output
    mock_client.scan.assert_called_once()


@patch("swb.cli.SWBClient")
def test_scan_with_options(mock_client_class: Mock, runner: CliRunner) -> None:
    """Test scan command with options."""
    from swb.models import ScanResponse, ScanTerm

    mock_scan_response = ScanResponse(
        terms=[
            ScanTerm(value="Python programming", number_of_records=100),
        ],
        scan_clause="pica.tit=Python",
    )

    mock_client = Mock()
    mock_client.scan.return_value = mock_scan_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(cli, ["scan", "pica.tit=Python", "--max", "5"])

    assert result.exit_code == 0
    call_args = mock_client.scan.call_args
    assert call_args is not None
    assert call_args.kwargs["scan_clause"] == "pica.tit=Python"
    assert call_args.kwargs["maximum_terms"] == 5


@patch("swb.cli.SWBClient")
def test_scan_no_results(mock_client_class: Mock, runner: CliRunner) -> None:
    """Test scan with no results."""
    from swb.models import ScanResponse

    mock_scan_response = ScanResponse(
        terms=[],
        scan_clause="pica.per=ZZZZZ",
    )

    mock_client = Mock()
    mock_client.scan.return_value = mock_scan_response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(cli, ["scan", "pica.per=ZZZZZ"])

    assert result.exit_code == 0
    assert "No terms found" in result.output


# Tests for resolve_base_url function
def test_resolve_base_url_with_custom_url():
    """Test that custom URL takes precedence over profile."""
    custom_url = "https://custom.example.com/sru"
    result = resolve_base_url(profile="k10plus", url=custom_url)
    assert result == custom_url


def test_resolve_base_url_with_profile():
    """Test URL resolution from profile name."""
    result = resolve_base_url(profile="k10plus", url=None)
    assert result == "https://sru.k10plus.de/opac-de-627"


def test_resolve_base_url_with_swb_profile():
    """Test URL resolution for SWB profile."""
    result = resolve_base_url(profile="swb", url=None)
    assert result == "https://sru.k10plus.de/swb"


def test_resolve_base_url_with_dnb_profile():
    """Test URL resolution for DNB profile."""
    result = resolve_base_url(profile="dnb", url=None)
    assert result == "https://services.dnb.de/sru/dnb"


def test_resolve_base_url_default():
    """Test that default profile (SWB) is used when neither profile nor URL provided."""
    result = resolve_base_url(profile=None, url=None)
    assert result == "https://sru.k10plus.de/swb"


def test_resolve_base_url_invalid_profile():
    """Test that invalid profile raises ValueError."""
    with pytest.raises(ValueError, match="Unknown profile: invalid"):
        resolve_base_url(profile="invalid", url=None)


# ---------------------------------------------------------------------------
# handle_api_error exit codes
# ---------------------------------------------------------------------------


class TestHandleApiErrorExitCodes:
    """Each exception type must map to its documented exit code."""

    @pytest.mark.parametrize(
        ("exception", "expected_code"),
        [
            (ValidationError("bad input"), 2),
            (AuthenticationError("forbidden", status_code=403), 3),
            (RateLimitError("slow down", status_code=429), 3),
            (ParseError("bad xml", xml_snippet="<broken>"), 4),
            (NetworkError("connection refused"), 5),
            (ServerError("boom", status_code=500), 5),
            (SWBError("generic"), 1),
            (RuntimeError("unexpected"), 99),
        ],
    )
    def test_exit_code(self, exception: Exception, expected_code: int) -> None:
        with pytest.raises(SystemExit) as exc_info:
            handle_api_error(exception, "https://example.org/sru")
        assert exc_info.value.code == expected_code


# ---------------------------------------------------------------------------
# Holdings display
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_holdings_response() -> SearchResponse:
    """Search response with one result covering all holding display cases."""
    return SearchResponse(
        total_results=1,
        results=[
            SearchResult(
                record_id="1",
                title="Faust",
                author="Goethe",
                year="1808",
                holdings=[
                    LibraryHolding(
                        library_code="DE-21",
                        library_name="Universität Tübingen",
                        collection="Main",
                    ),
                    LibraryHolding(
                        library_code="DE-M504105",
                        library_name="Onleihe",
                        access_url="https://onleihe.example",
                        access_note="Titel nur digital verfügbar",
                    ),
                    LibraryHolding(library_code="DE-999XYZ", library_name=None),
                    LibraryHolding(library_code="", library_name=None),
                ],
            )
        ],
        query='pica.all="Faust"',
    )


def _make_mock_client(mock_client_class: Mock, response: SearchResponse) -> Mock:
    mock_client = Mock()
    mock_client.search.return_value = response
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client
    return mock_client


@patch("swb.cli.SWBClient")
def test_search_holdings_display(
    mock_client_class: Mock,
    runner: CliRunner,
    mock_holdings_response: SearchResponse,
) -> None:
    """Known name shows 'Name (CODE)', unknown shows code, empty shows fallback."""
    _make_mock_client(mock_client_class, mock_holdings_response)

    result = runner.invoke(cli, ["search", "Faust", "--holdings"])

    assert result.exit_code == 0
    assert "Universität Tübingen" in result.output
    assert "(DE-21)" in result.output
    assert "Onleihe" in result.output
    assert "(DE-M504105)" in result.output
    # Unknown code is shown as-is, without a generic prefix
    assert "DE-999XYZ" in result.output
    assert "German Library" not in result.output
    assert "Unknown Library" in result.output


@patch("swb.cli.SWBClient")
def test_search_no_holdings_available(
    mock_client_class: Mock,
    runner: CliRunner,
    mock_search_response: SearchResponse,
) -> None:
    """Records without holdings show an informative note."""
    _make_mock_client(mock_client_class, mock_search_response)

    result = runner.invoke(cli, ["search", "Python", "--holdings"])

    assert result.exit_code == 0
    assert "No holdings information available" in result.output


# ---------------------------------------------------------------------------
# Output file, raw mode, facets
# ---------------------------------------------------------------------------


@patch("swb.cli.SWBClient")
def test_search_output_file(
    mock_client_class: Mock,
    runner: CliRunner,
    mock_holdings_response: SearchResponse,
    tmp_path: Path,
) -> None:
    """--output writes record details including holdings to a file."""
    _make_mock_client(mock_client_class, mock_holdings_response)
    output_file = tmp_path / "results.txt"

    result = runner.invoke(
        cli,
        ["search", "Faust", "--holdings", "--output", str(output_file)],
    )

    assert result.exit_code == 0
    content = output_file.read_text()
    assert "Title: Faust" in content
    assert "Author: Goethe" in content
    assert "Library: Universität Tübingen" in content
    assert "Access URL: https://onleihe.example" in content


@patch("swb.cli.SWBClient")
def test_search_raw_output(
    mock_client_class: Mock,
    runner: CliRunner,
) -> None:
    """--raw prints the raw record data."""
    response = SearchResponse(
        total_results=1,
        results=[
            SearchResult(
                record_id="1",
                title="Faust",
                raw_data="<record><title>Faust</title></record>",
            )
        ],
        query="q",
    )
    _make_mock_client(mock_client_class, response)

    result = runner.invoke(cli, ["search", "Faust", "--raw"])

    assert result.exit_code == 0
    assert "Raw Data" in result.output
    assert "<title>Faust</title>" in result.output


@patch("swb.cli.SWBClient")
def test_search_facets_display(
    mock_client_class: Mock,
    runner: CliRunner,
) -> None:
    """Facets returned by the server are rendered with counts."""
    response = SearchResponse(
        total_results=1,
        results=[SearchResult(record_id="1", title="Faust")],
        query="q",
        facets=[
            Facet(
                name="year",
                values=[FacetValue(value="2024", count=12), FacetValue("2023", 7)],
            )
        ],
    )
    _make_mock_client(mock_client_class, response)

    result = runner.invoke(cli, ["search", "Faust", "--facets", "year"])

    assert result.exit_code == 0
    assert "Facets" in result.output
    assert "year" in result.output
    assert "2024" in result.output
    assert "12" in result.output


# ---------------------------------------------------------------------------
# Error paths through the CLI
# ---------------------------------------------------------------------------


@patch("swb.cli.SWBClient")
def test_search_validation_error_exit_code(
    mock_client_class: Mock,
    runner: CliRunner,
) -> None:
    """A ValidationError from the client leads to exit code 2."""
    mock_client = Mock()
    mock_client.search.side_effect = ValidationError("empty query")
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(cli, ["search", "Python"])

    assert result.exit_code == 2


@patch("swb.cli.SWBClient")
def test_search_network_error_exit_code(
    mock_client_class: Mock,
    runner: CliRunner,
) -> None:
    """A NetworkError from the client leads to exit code 5."""
    mock_client = Mock()
    mock_client.search.side_effect = NetworkError("connection refused")
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(cli, ["search", "Python"])

    assert result.exit_code == 5
