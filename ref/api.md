# SWBClient Reference (`src/swb/api.py`)

## Constructor

```python
SWBClient(
    base_url: str | None = None,   # defaults to official SWB SRU endpoint
    timeout: int = 30,
    api_key: str | None = None,
    rate_limit: int | None = None, # max requests/second, sliding window; None = no limit
)
```

Supports context manager (`with SWBClient() as client: ...`); `close()` closes the
requests session.

## Public methods

| Method | Key parameters | Returns |
|--------|----------------|---------|
| `search(query, ...)` | `record_format`, `start_record=1`, `maximum_records=10`, `index`, `sort_by`, `sort_order`, `record_packing="xml"`, `facets`, `facet_limit=10`, `sru_version` | `SearchResponse` |
| `search_by_isbn(isbn, ...)` | `record_format`, `record_packing` (no max/start params) | `SearchResponse` |
| `search_by_issn(issn, ...)` | `record_format`, `record_packing` | `SearchResponse` |
| `scan(scan_clause, ...)` | `response_position=1`, `maximum_terms=20`; clause is full CQL, e.g. `"pica.tit=Python"` (no separate `index` param) | `ScanResponse` |
| `explain()` | — | `ExplainResponse` |
| `search_related(ppn, relation_type, ...)` | `record_type`, `record_format`, paging, sorting, packing | `SearchResponse` |

## Error handling

Validation failures raise `ValidationError`; XML problems raise `ParseError`
(with `xml_snippet`); connection problems raise `NetworkError`; HTTP status maps to
`AuthenticationError` (403), `RateLimitError` (429), `ServerError` (5xx), else `APIError`.
`_handle_http_errors()` checks `response.status_code` — mocks in tests must set it.

CLI exit codes (`cli.py: handle_api_error`):

| Code | Meaning |
|------|---------|
| 0 | success |
| 2 | `ValidationError` |
| 3 | `AuthenticationError` / `RateLimitError` |
| 4 | `ParseError` |
| 5 | `NetworkError` / `ServerError` / other `APIError` |
| 99 | unexpected exception |

## Holdings parsing

Holdings come from MARC field 924; subfield `$b` is the ISIL library code,
`$k` access URL, `$l` access note.

Library name resolution (`api.py` around line 1160):
- `LIBRARY_NAMES` dict maps ~90 verified ISIL codes to names (built from real SWB
  holdings + lobid.org organisations API)
- Codes starting `DE-M504` are Onleihe (digital lending) services: name = "Onleihe"
- `LFER` is a fictitious library marking freely accessible e-resources in SWB/K10plus
- Any other unknown code: `library_name = None`; the CLI then displays just the code
- ISIL registry for lookups: https://sigel.staatsbibliothek-berlin.de/

## Parsing internals

`_parse_response` dispatches per `RecordFormat` to `_parse_marcxml`, `_parse_turbomarc`,
`_parse_mods`, etc. XML is parsed with the hardened module-level `SECURE_PARSER`
(lxml, entity resolution disabled). Facets parsed by `_parse_facets` (SRU 2.0 only).
