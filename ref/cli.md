# CLI Reference (`src/swb/cli.py`)

Click group `cli`, entry point `swb`. Root options: `--verbose`, `--quiet`.
Output uses Rich (tables, panels); errors go to stderr with exit codes (see [api.md](api.md)).

## Commands

| Command | Argument | Options |
|---------|----------|---------|
| `search` | `query` | `--index --format --max --start-record --raw --output --profile --url --sort-by --sort-order --packing --holdings --facets --facet-limit` |
| `isbn` | `isbn` | `--format --raw --output --profile --url --packing --holdings` |
| `issn` | `issn` | `--format --raw --output --profile --url --packing --holdings` |
| `related` | `ppn` | `--relation-type --record-type --format --max --start-record --raw --output --profile --url --sort-by --sort-order --packing --holdings` |
| `scan` | `scan_clause` | `--max --position --profile --url` |
| `explain` | — | `--profile --url` |
| `formats` | — | lists record formats |
| `indices` | — | lists search indices |
| `profiles` | — | lists catalog profiles |

## Key helpers

- `resolve_base_url(url, profile)` — `--url` wins over `--profile`, default profile `swb`
- `display_results(...)` — Rich tables; holdings table shows
  `"Name (CODE)"` for known libraries, just `CODE` for unknown ones
- `handle_api_error(e, base_url)` — maps exceptions to messages + exit codes
- `main()` — script entry point

## Examples

```bash
swb search "Faust Goethe" --max 5 --holdings
swb search "Python" --index tit --sort-by year --profile k10plus
swb isbn 978-3-16-148410-0
swb scan "pica.tit=Python" --max 10
swb explain --profile dnb
```
