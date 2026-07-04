# Architecture

Python 3.12+ client for German library catalogs via the SRU protocol (Search/Retrieve via URL).
Primary target is the SWB (Suedwestdeutscher Bibliotheksverbund); also supports K10plus, GVK,
DNB, BVB and HEBIS via profiles.

## Entry points (pyproject.toml)

| Script | Target |
|--------|--------|
| `swb` | `swb.cli:main` (Click CLI) |
| `swb-tui` | `swb.tui:run_tui` (Textual TUI, needs extra `tui`) |

## Module map (`src/swb/`)

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `api.py` | ~1670 | `SWBClient`: HTTP calls, XML parsing, holdings, rate limiting. See [api.md](api.md) |
| `cli.py` | ~1190 | Click CLI with 9 commands, Rich output. See [cli.md](cli.md) |
| `models.py` | ~290 | Enums and dataclasses (all frozen data, no logic beyond `has_more`) |
| `exceptions.py` | ~110 | Exception hierarchy + `format_error_message()` |
| `profiles.py` | ~100 | `CatalogProfile`, `PROFILES` dict (6 catalogs), `get_profile()`, `list_profiles()` |
| `tui.py` | ~380 | Experimental Textual TUI (`SWBTUIDirect`), barely tested (3% coverage) |
| `__init__.py` | ~75 | Re-exports client, models, exceptions; optional TUI import |

## models.py

- Enums: `RecordFormat` (marcxml, marcxml-legacy, mods, picaxml, dc, isbd, turbomarc, mads),
  `SearchIndex` (pica.tit, pica.per, pica.sub, pica.isb, pica.iss, pica.vlg, pica.ejr,
  pica.all, pica.woe), `SortBy`, `SortOrder`, `RelationType` (fam, rel-bt, rel-nt, rel-rt,
  rel-tt), `RecordType` (b=bibliographic, n=authority)
- Dataclasses: `SearchResult`, `SearchResponse` (with `has_more` property), `LibraryHolding`,
  `Facet`/`FacetValue`, `ScanResponse`/`ScanTerm`,
  `ExplainResponse`/`ServerInfo`/`DatabaseInfo`/`IndexInfo`/`SchemaInfo`

## exceptions.py

```
SWBError
├── ConfigurationError
├── ValidationError
├── APIError (status_code attr)
│   ├── AuthenticationError   (403)
│   ├── RateLimitError        (429)
│   └── ServerError           (5xx)
├── ParseError (xml_snippet attr)
└── NetworkError
```

## profiles.py

`PROFILES` keys: `swb` (default), `k10plus`, `gvk`, `dnb`, `bvb`, `hebis`.
Each `CatalogProfile` has name, url, display_name, description, region.

## Other docs

- `docs/` — MkDocs user documentation (Material theme, deployed via GitHub Actions)
- `progress.md`, `todo.md` — session status and improvement backlog
- `tests/` — see [testing.md](testing.md)
