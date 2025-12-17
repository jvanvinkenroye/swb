"""Tests for the CLI interface."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from swb.cli import cli
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
        "978-3-16-148410-0", record_format=RecordFormat.MARCXML
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
        "0028-0836", record_format=RecordFormat.MARCXML
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
