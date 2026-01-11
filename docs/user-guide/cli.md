# Command Line Interface

Complete reference for all CLI commands and options.

## Global Options

Available for all commands:

```bash
swb [OPTIONS] COMMAND [ARGS]
```

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--verbose`, `-v` | Enable verbose output (DEBUG level) |
| `--quiet`, `-q` | Quiet mode (errors only) |
| `--help` | Show help message |

## Commands

### search

Search the catalog with a query.

```bash
swb search [OPTIONS] QUERY
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--index` | `-i` | `title` | Search index to use |
| `--format` | `-f` | `marcxml` | Record format |
| `--max` | `-m` | `10` | Maximum number of records |
| `--start-record` | | `1` | Starting record position |
| `--sort-by` | | | Sort results by field |
| `--sort-order` | | `descending` | Sort order |
| `--output` | `-o` | | Save results to file |
| `--raw` | | | Include raw XML in output |
| `--holdings` | | | Show library holdings |
| `--packing` | | `xml` | Record packing mode |
| `--profile` | `-p` | `swb` | Library catalog profile |
| `--url` | | | Custom SRU endpoint URL |

**Examples:**

```bash
# Basic search
swb search "Python programming"

# Search with options
swb search "Goethe" --index author --max 20 --sort-by year

# Search with holdings
swb search "Machine Learning" --holdings --profile k10plus

# Save results
swb search "Python" --output results.txt --raw
```

### isbn

Search by ISBN number.

```bash
swb isbn [OPTIONS] ISBN
```

**Options:** Same as `search` command

**Examples:**

```bash
# Basic ISBN search
swb isbn 978-3-16-148410-0

# With holdings
swb isbn 978-3-16-148410-0 --holdings

# Different profile
swb isbn 978-3-16-148410-0 --profile dnb
```

### issn

Search by ISSN number.

```bash
swb issn [OPTIONS] ISSN
```

**Options:** Same as `search` command

**Examples:**

```bash
swb issn 0028-0836
swb issn 0028-0836 --holdings --profile k10plus
```

### related

Search for related records (multi-volume works, series).

```bash
swb related [OPTIONS] PPN
```

**Options:**

| Option | Description |
|--------|-------------|
| `--relation-type` | Type of relation (child, parent, family, related, thesaurus) |
| `--record-type` | Record type (bibliographic, authority) |
| Plus all search options | |

**Examples:**

```bash
# Find volumes of a multi-volume work
swb related 267838395 --relation-type child

# Find parent record
swb related 123456789 --relation-type parent

# Find entire family
swb related 267838395 --relation-type family --max 50
```

### scan

Browse index terms for auto-completion.

```bash
swb scan [OPTIONS] SCAN_CLAUSE
```

**Options:**

| Option | Description |
|--------|-------------|
| `--max` | Maximum terms to return |
| `--position` | Starting position in term list |
| `--profile` | Library catalog profile |
| `--url` | Custom SRU endpoint |

**Examples:**

```bash
# Find authors starting with "Goe"
swb scan "pica.per=Goe"

# Find titles
swb scan "pica.tit=Python" --max 20

# Different profile
swb scan "pica.per=Goethe" --profile dnb
```

### explain

Get server capabilities and configuration.

```bash
swb explain [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--profile` | Library catalog profile |
| `--url` | Custom SRU endpoint |

**Examples:**

```bash
# Default server
swb explain

# Different profiles
swb explain --profile k10plus
swb explain --profile dnb
```

### profiles

List available library catalog profiles.

```bash
swb profiles
```

No options. Shows table of all configured profiles.

### formats

List available record formats.

```bash
swb formats
```

Shows all supported output formats.

### indices

List available search indices.

```bash
swb indices
```

Shows all searchable indices with descriptions.

## Search Indices

| Index | CQL Name | Description |
|-------|----------|-------------|
| title | pica.tit | Title search |
| author | pica.per | Person/Author |
| subject | pica.sub | Subject headings |
| isbn | pica.isb | ISBN number |
| issn | pica.iss | ISSN number |
| keyword | pica.woe | Keyword search |
| all | pica.all | All fields |
| publisher | pica.vlg | Publisher |
| year | pica.ejr | Publication year |

## Record Formats

| Format | Description |
|--------|-------------|
| marcxml | MARC 21 XML (default) |
| marcxml-legacy | MARC 21 XML Legacy |
| turbomarc | TurboMARC |
| mods | MODS |
| mods36 | MODS 3.6 |
| picaxml | PICA XML |
| dc | Dublin Core |
| isbd | ISBD format |
| mads | MADS format |

## CQL Queries

Use full CQL syntax in search queries:

```bash
# Boolean operators
swb search 'pica.tit="Python" and pica.per="Guido"'

# Wildcards
swb search 'pica.tit="Pytho*"'

# Date ranges
swb search 'pica.tit="Python" and pica.ejr>2020'

# Multiple conditions
swb search 'pica.tit="Machine Learning" and pica.ejr=2023'
```

## Output Redirection

```bash
# Redirect output
swb search "Python" > results.txt

# Append to file
swb search "Python" >> results.txt

# Error output
swb search "Python" 2> errors.txt

# Both
swb search "Python" > results.txt 2> errors.txt
```

## Pipelines

Combine with other tools:

```bash
# Count results
swb search "Python" | grep "Title:" | wc -l

# Extract ISBNs
swb search "Python" --max 50 | grep "ISBN:" | cut -d: -f2

# Search and process
swb search "Python" --output - | python process.py
```

## Environment Variables

```bash
# Set log level
export LOG_LEVEL=DEBUG
swb search "Python"

# Custom config location
export SWB_CONFIG_DIR=~/.config/swb
```

## Shell Completion

See [Installation](installation.md#optional-shell-completion) for setup.

Once configured:

```bash
# Tab completion
swb <TAB>
swb search --<TAB>
swb --profile <TAB>
```

## Tips & Tricks

### Aliases

Add to your shell config:

```bash
# ~/.bashrc or ~/.zshrc
alias swbs='swb search'
alias swbi='swb isbn'
alias swbh='swb search --holdings'
```

### Quick Searches

```bash
# Create function for common searches
books() {
    swb search "$1" --index title --max 20 --holdings
}

books "Python programming"
```

### Multiple Profiles

```bash
# Search across catalogs
for profile in swb k10plus dnb; do
    echo "=== $profile ==="
    swb isbn 978-3-16-148410-0 --profile $profile --holdings
done
```

## Next Steps

- [Advanced Features](advanced.md) - CQL, scanning, more
- [API Reference](../api/overview.md) - Use in Python code
