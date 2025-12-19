"""Tests for the CLI interface."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from swb.cli import cli, resolve_base_url
from swb.models import RecordFormat, SearchResponse, SearchResult


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
