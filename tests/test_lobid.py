"""Tests for the lobid-resources client (hbz backend)."""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
import requests

from swb.cli import create_client
from swb.exceptions import (
    APIError,
    NetworkError,
    ParseError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from swb.lobid import DEFAULT_LOBID_URL, LobidClient
from swb.models import SearchIndex, SortBy

SAMPLE_MEMBER: dict[str, Any] = {
    "id": "http://lobid.org/resources/990212549810206441#!",
    "almaMmsId": "990212549810206441",
    "hbzId": "HT019025795",
    "title": "Das Kapital",
    "otherTitleInformation": ["Schuld - Territorium - Utopie"],
    "isbn": ["9783862065752", "3862065758"],
    "publication": [
        {
            "startDate": "2016",
            "location": ["Dortmund"],
            "publishedBy": ["Verlag Kettler"],
        }
    ],
    "contribution": [
        {
            "agent": {"label": "Nichols, Catherine"},
            "role": {
                "id": "http://id.loc.gov/vocabulary/relators/edt",
                "label": "Herausgeber/in",
            },
        },
        {
            "agent": {"label": "Melville, Herman"},
            "role": {
                "id": "http://id.loc.gov/vocabulary/relators/aut",
                "label": "Autor/in",
            },
        },
    ],
    "hasItem": [
        {
            "callNumber": "3C 40977",
            "heldBy": {
                "isil": "DE-6",
                "label": "Universitäts- und Landesbibliothek Münster",
            },
            "seeAlso": ["https://hbz-ulbms.primo.exlibrisgroup.com/example"],
        },
        {
            "heldBy": {"isil": "DE-82"},
        },
    ],
}


def make_client_with_response(
    payload: dict[str, Any] | None = None,
    status_code: int = 200,
    text: str = "",
) -> tuple[LobidClient, MagicMock]:
    """Create a LobidClient whose session returns a mocked response."""
    client = LobidClient()
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = text or json.dumps(payload or {})
    if payload is not None:
        mock_response.json.return_value = payload
    else:
        mock_response.json.side_effect = ValueError("no JSON")
    client.session = MagicMock()
    client.session.get.return_value = mock_response
    return client, client.session.get


class TestLobidQueryBuilding:
    """Tests for query translation to lobid/Lucene syntax."""

    @pytest.mark.parametrize(
        ("index", "query", "expected"),
        [
            (SearchIndex.TITLE, "Faust", 'title:"Faust"'),
            (
                SearchIndex.AUTHOR,
                "Melville",
                'contribution.agent.label:"Melville"',
            ),
            (SearchIndex.SUBJECT, "Kunst", 'subjectslabels:"Kunst"'),
            (SearchIndex.ISBN, "9783862065752", 'isbn:"9783862065752"'),
            (None, "freitext suche", "freitext suche"),
            (SearchIndex.ALL, "alles", "alles"),
        ],
    )
    def test_query_translation(
        self, index: SearchIndex | None, query: str, expected: str
    ) -> None:
        client, mock_get = make_client_with_response(
            {"totalItems": 0, "member": []}
        )
        client.search(query, index=index)
        params = mock_get.call_args.kwargs["params"]
        assert params["q"] == expected

    def test_quotes_in_query_are_escaped(self) -> None:
        client, mock_get = make_client_with_response(
            {"totalItems": 0, "member": []}
        )
        client.search('Das "Kapital"', index=SearchIndex.TITLE)
        params = mock_get.call_args.kwargs["params"]
        assert params["q"] == 'title:"Das \\"Kapital\\""'

    def test_pagination_params(self) -> None:
        client, mock_get = make_client_with_response(
            {"totalItems": 0, "member": []}
        )
        client.search("test", start_record=11, maximum_records=5)
        params = mock_get.call_args.kwargs["params"]
        assert params["from"] == 10
        assert params["size"] == 5

    def test_owner_filter(self) -> None:
        client, mock_get = make_client_with_response(
            {"totalItems": 0, "member": []}
        )
        client.search("test", owner="DE-6,DE-82")
        params = mock_get.call_args.kwargs["params"]
        assert params["owner"] == "DE-6,DE-82"

    def test_isbn_search_strips_hyphens(self) -> None:
        client, mock_get = make_client_with_response(
            {"totalItems": 0, "member": []}
        )
        client.search_by_isbn("978-3-86206-575-2")
        params = mock_get.call_args.kwargs["params"]
        assert params["q"] == 'isbn:"9783862065752"'

    def test_issn_search_strips_hyphens(self) -> None:
        client, mock_get = make_client_with_response(
            {"totalItems": 0, "member": []}
        )
        client.search_by_issn("1618-7792")
        params = mock_get.call_args.kwargs["params"]
        assert params["q"] == 'issn:"16187792"'


class TestLobidValidation:
    """Tests for rejected parameters."""

    def test_empty_query_raises(self) -> None:
        client, _ = make_client_with_response({"totalItems": 0, "member": []})
        with pytest.raises(ValidationError):
            client.search("   ")

    def test_sort_by_raises(self) -> None:
        client, _ = make_client_with_response({"totalItems": 0, "member": []})
        with pytest.raises(ValidationError, match="Sorting"):
            client.search("test", sort_by=SortBy.YEAR)

    def test_facets_raise(self) -> None:
        client, _ = make_client_with_response({"totalItems": 0, "member": []})
        with pytest.raises(ValidationError, match="Facets"):
            client.search("test", facets=["year"])

    def test_scan_raises(self) -> None:
        client = LobidClient()
        with pytest.raises(ValidationError, match="Scan"):
            client.scan(scan_clause="pica.tit=Python")

    def test_explain_raises(self) -> None:
        client = LobidClient()
        with pytest.raises(ValidationError, match="Explain"):
            client.explain()

    def test_search_related_raises(self) -> None:
        client = LobidClient()
        with pytest.raises(ValidationError, match="Related"):
            client.search_related(ppn="123")


class TestLobidParsing:
    """Tests for mapping lobid JSON onto the shared models."""

    def test_parse_full_member(self) -> None:
        client, _ = make_client_with_response(
            {"totalItems": 1, "member": [SAMPLE_MEMBER]}
        )
        response = client.search("Kapital")

        assert response.total_results == 1
        result = response.results[0]
        assert result.record_id == "990212549810206441"
        assert result.title == "Das Kapital : Schuld - Territorium - Utopie"
        # The aut role is preferred over other contributions
        assert result.author == "Melville, Herman"
        assert result.year == "2016"
        assert result.publisher == "Verlag Kettler"
        assert result.isbn == "9783862065752, 3862065758"
        assert result.link == "http://lobid.org/resources/990212549810206441#!"
        assert result.raw_data is not None
        assert "almaMmsId" in result.raw_data

    def test_parse_holdings(self) -> None:
        client, _ = make_client_with_response(
            {"totalItems": 1, "member": [SAMPLE_MEMBER]}
        )
        result = client.search("Kapital").results[0]

        assert result.holdings is not None
        assert len(result.holdings) == 2
        first = result.holdings[0]
        assert first.library_code == "DE-6"
        assert (
            first.library_name == "Universitäts- und Landesbibliothek Münster"
        )
        assert (
            first.access_url
            == "https://hbz-ulbms.primo.exlibrisgroup.com/example"
        )
        assert first.access_note == "Signatur: 3C 40977"
        # Item without seeAlso/callNumber still yields code and name=None
        second = result.holdings[1]
        assert second.library_code == "DE-82"
        assert second.access_url is None

    def test_author_fallback_without_aut_role(self) -> None:
        member = {
            "title": "Testbuch",
            "contribution": [
                {
                    "agent": {"label": "Nichols, Catherine"},
                    "role": {
                        "id": "http://id.loc.gov/vocabulary/relators/edt"
                    },
                }
            ],
        }
        client, _ = make_client_with_response(
            {"totalItems": 1, "member": [member]}
        )
        result = client.search("Testbuch").results[0]
        assert result.author == "Nichols, Catherine"

    def test_empty_result(self) -> None:
        client, _ = make_client_with_response({"totalItems": 0, "member": []})
        response = client.search("nichts")
        assert response.total_results == 0
        assert response.results == []
        assert response.next_record is None

    def test_pagination_next_record(self) -> None:
        client, _ = make_client_with_response(
            {"totalItems": 100, "member": [SAMPLE_MEMBER]}
        )
        response = client.search("Kapital", start_record=1, maximum_records=1)
        assert response.next_record == 2
        assert response.has_more


class TestLobidErrors:
    """Tests for HTTP and parse error mapping."""

    def test_server_error(self) -> None:
        client, _ = make_client_with_response({}, status_code=500)
        with pytest.raises(ServerError):
            client.search("test")

    def test_rate_limit_error(self) -> None:
        client, _ = make_client_with_response({}, status_code=429)
        with pytest.raises(RateLimitError):
            client.search("test")

    def test_other_http_error(self) -> None:
        client, _ = make_client_with_response({}, status_code=404)
        with pytest.raises(APIError) as exc_info:
            client.search("test")
        assert exc_info.value.status_code == 404

    def test_invalid_json_raises_parse_error(self) -> None:
        client, _ = make_client_with_response(None, text="<html>not json")
        with pytest.raises(ParseError):
            client.search("test")

    def test_connection_error_raises_network_error(self) -> None:
        client = LobidClient()
        client.session = MagicMock()
        client.session.get.side_effect = requests.ConnectionError("refused")
        with pytest.raises(NetworkError):
            client.search("test")


class TestCreateClient:
    """Tests for CLI client selection."""

    def test_hbz_profile_returns_lobid_client(self) -> None:
        client = create_client("hbz", None)
        assert isinstance(client, LobidClient)
        assert client.base_url == DEFAULT_LOBID_URL
        client.close()

    def test_sru_profile_returns_swb_client(self) -> None:
        from swb.api import SWBClient

        client = create_client("swb", None)
        assert isinstance(client, SWBClient)
        client.close()

    def test_custom_url_wins_over_hbz_profile(self) -> None:
        from swb.api import SWBClient

        client = create_client("hbz", "https://example.org/sru")
        assert isinstance(client, SWBClient)
        client.close()
