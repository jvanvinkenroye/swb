# Getting Started

This guide will walk you through the basics of using the SWB API Client.

## Your First Search

The simplest way to start is with a basic search:

```bash
swb search "Python programming"
```

This will search for books about Python programming in the default SWB catalog and display formatted results with titles, authors, and publication years.

## Understanding the Output

A typical search result looks like this:

```
Record 1:
  Title: Python Programming: An Introduction to Computer Science
  Author: Zelle, John
  Year: 2016
  Publisher: Franklin, Beedle & Associates
  ISBN: 978-1-59028-241-0
```

## Basic Commands

### Search by Keyword

```bash
# Simple keyword search
swb search "Machine Learning"

# Search in specific index
swb search "Goethe" --index author

# Limit number of results
swb search "Python" --max 10
```

### Search by ISBN

```bash
swb isbn 978-3-16-148410-0
```

### Search by ISSN

```bash
swb issn 0028-0836
```

### List Available Options

```bash
# Show available record formats
swb formats

# Show searchable indices
swb indices

# Show library catalog profiles
swb profiles
```

## Using Different Catalogs

The SWB client supports multiple German library catalogs:

```bash
# Search in K10plus catalog (covers more of Germany)
swb search "Python" --profile k10plus

# Search in German National Library
swb isbn 978-3-16-148410-0 --profile dnb

# Search in Bavarian Library Network
swb search "Goethe" --profile bvb
```

Available profiles:

- `swb` - Southwestern Germany (default)
- `k10plus` - Northern and southwestern Germany
- `dnb` - German National Library
- `gvk` - Northern Germany
- `bvb` - Bavaria
- `hebis` - Hesse and parts of Rhineland-Palatinate

## Viewing Library Holdings

To see which libraries have a book and how to access it:

```bash
# Show holdings for an ISBN
swb isbn 978-3-17-025295-0 --holdings

# Show holdings in search results
swb search "Autismus" --holdings --max 3
```

The holdings display shows:

- Library names and locations
- Online access URLs
- Access restrictions (VPN, campus-only, etc.)
- Collections and call numbers

## Sorting Results

Sort search results by different criteria:

```bash
# Sort by year (newest first)
swb search "Python" --sort-by year

# Sort by year (oldest first)
swb search "Python" --sort-by year --sort-order ascending

# Sort by author
swb search "Machine Learning" --sort-by author
```

## Saving Results

Export search results to a file:

```bash
# Save formatted output
swb search "Python" --output results.txt

# Include raw XML data
swb search "Python" --output results.txt --raw
```

## Interactive Terminal UI

For a more user-friendly experience, try the interactive TUI:

```bash
swb-tui
```

The TUI provides:

- **Ctrl+S** - Execute search
- **Ctrl+C** - Clear results
- **Ctrl+Q** - Quit application
- Dropdown menus for all options
- Scrollable results

See the [TUI Guide](tui.md) for more details.

## Common Use Cases

### Finding a Specific Book

If you know the ISBN:

```bash
swb isbn 978-3-16-148410-0 --holdings
```

### Finding Books by an Author

```bash
swb search "Goethe" --index author --max 20
```

### Finding Recent Publications

```bash
swb search "Artificial Intelligence" --sort-by year --max 10
```

### Browsing a Subject

```bash
swb search "pica.sub=Informatik" --max 50
```

### Checking Multiple Catalogs

```bash
# Check SWB
swb isbn 978-3-16-148410-0 --holdings

# Check K10plus for more libraries
swb isbn 978-3-16-148410-0 --holdings --profile k10plus

# Check DNB for national holdings
swb isbn 978-3-16-148410-0 --profile dnb
```

## Getting Help

Every command has built-in help:

```bash
# General help
swb --help

# Command-specific help
swb search --help
swb isbn --help
swb profiles --help
```

## Troubleshooting

### No Results Found

If your search returns no results:

1. **Check spelling** - Try wildcards: `"Pytho*"`
2. **Broaden search** - Use fewer keywords
3. **Try different index** - Switch from title to keyword search
4. **Check catalog** - Some books may only be in specific catalogs

### Connection Timeouts

The client uses a 30-second timeout. For slow connections:

```python
from swb import SWBClient

# Increase timeout to 60 seconds
client = SWBClient(timeout=60)
```

### Server Errors (403 Forbidden)

If you get access denied errors:

- Try a different profile (`--profile k10plus` or `--profile dnb`)
- Check if your IP is blocked
- Some catalogs may require VPN access

## Next Steps

Now that you know the basics:

- [Terminal UI Guide](tui.md) - Explore the interactive interface
- [CLI Reference](cli.md) - Learn all CLI commands
- [Library Profiles](profiles.md) - Understand catalog profiles
- [Advanced Features](advanced.md) - CQL queries, scanning, and more
