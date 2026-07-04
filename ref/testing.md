# Testing Reference (`tests/`)

179 tests total: 160 unit + 19 integration. Coverage ~71% (weak spot: `tui.py` ~3%;
`cli.py` at ~72%).

## Running

```bash
uv run pytest                       # everything incl. integration (real API calls)
uv run pytest -m "not integration"  # unit tests only (fast, offline)
uv run pytest -m "integration and not slow"
```

Coverage is on by default via pyproject addopts (`--cov=swb`, terminal + `htmlcov/`).
Markers: `integration` (real network calls), `slow`.

## Test files

| File | Tests | Covers |
|------|-------|--------|
| `test_api.py` | 43 | Client methods, XML parsing per format, holdings |
| `test_api_validation.py` | 27 | Input validation (`ValidationError` cases) |
| `test_cli.py` | 37 | CLI commands, exit codes, holdings display, --output/--raw/facets |
| `test_edge_cases.py` | 22 | Network errors, HTTP errors, malformed XML, encoding |
| `test_integration.py` | 19 | Real SRU API calls (search, isbn, scan, explain) |
| `test_models.py` | 6 | Dataclasses/enums |
| `test_profiles.py` | 14 | Profile lookup |
| `test_rate_limiting.py` | 11 | Sliding-window rate limiter |

## Conventions

- Mocked HTTP responses MUST set `mock_response.status_code = 200` — the client's
  `_handle_http_errors` reads it and a bare Mock breaks integer comparison.
- Expect custom exceptions, not builtins: `ValidationError` (not `ValueError`),
  `ParseError` for bad XML (message "XML Parse Error"), `NetworkError` for connection
  issues.
- Unknown library codes in holdings yield `library_name is None`
  (see `test_parse_holdings_unknown_library`).
- `search_by_isbn`/`search_by_issn` take no `maximum_records`; `scan` takes a full CQL
  clause (`"pica.tit=..."`) and no `index` parameter.
