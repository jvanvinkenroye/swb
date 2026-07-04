# SWB API Client

Python 3.12+ CLI/TUI client for German library catalogs (SWB, K10plus, DNB, GVK, BVB,
HEBIS) via the SRU protocol. Package `swb`, entry points `swb` (CLI) and `swb-tui` (TUI).

## Commands

```bash
uv run pytest -m "not integration"   # unit tests (fast, offline)
uv run pytest                        # all tests incl. real API calls
uv run ruff check src tests          # lint (line length 88, py312)
uv run ruff format src tests
uv run mypy src                      # strict-ish typing
uv run swb search "Goethe" --max 5   # try the CLI
uv run mkdocs build                  # user docs
```

Always use `uv` (never pip, never global installs).

## Reference docs (read these before diving into large source files)

- `ref/architecture.md` — module map, entry points, models, exception hierarchy, profiles
- `ref/api.md` — `SWBClient` methods, error handling, exit codes, holdings/library-name logic
- `ref/cli.md` — all CLI commands and options
- `ref/testing.md` — test layout, markers, mock conventions
- `ref/skill.md` — how the personal Claude skill "swb-buchsuche" uses this CLI

`api.py` (~1670 lines) and `cli.py` (~1190 lines) are large — check the ref docs first.

## Other documentation

- `docs/` — MkDocs user documentation (Material theme, auto-deployed to GitHub Pages)
- `progress.md` — session status log
- `todo.md` — improvement backlog

## Conventions

- Custom exceptions from `swb.exceptions` (never bare `ValueError` in the client)
- Mocked HTTP responses in tests need `status_code = 200`
- Library holdings: unknown ISIL codes get `library_name=None`; DE-M504xxx = Onleihe
- Conventional commits; no emojis in code or output
