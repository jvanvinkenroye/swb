# Terminal User Interface (TUI)

The SWB client includes an experimental interactive terminal UI powered by [Textual](https://textual.textualize.io/), providing a user-friendly way to explore library catalogs without memorizing CLI commands.

## Launching the TUI

Start the interactive interface:

```bash
swb-tui
```

The TUI will open in your terminal with a clean, organized interface.

## Interface Overview

The TUI consists of several sections:

### Search Form

At the top, you'll find the search form with:

- **Query Input** - Enter your search terms
- **Search Index** - Dropdown to select where to search (title, author, ISBN, etc.)
- **Record Format** - Choose output format (MARCXML, MODS, etc.)
- **Max Records** - Limit number of results
- **Search Button** - Execute the search

### Results Display

Below the form, search results appear in a scrollable container showing:

- Record number
- Title
- Author
- Publication year
- Publisher
- ISBN (when available)

### Status Messages

- **Loading indicators** during searches
- **Error messages** with helpful suggestions
- **Result counts** and status updates

## Keyboard Shortcuts

The TUI is designed for keyboard-driven workflows:

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Execute search |
| `Ctrl+C` | Clear results |
| `Ctrl+Q` | Quit application |
| `Tab` | Move to next field |
| `Shift+Tab` | Move to previous field |
| `↑` `↓` | Navigate dropdowns/results |
| `Enter` | Confirm selection |
| `Esc` | Close dropdown |

!!! tip "Efficient Navigation"
    Use `Tab` to quickly move between fields and `Ctrl+S` to search without reaching for the mouse.

## Search Workflow

### Basic Search

1. Enter search terms in the Query field
2. (Optional) Select search index from dropdown
3. Press `Ctrl+S` or click Search button
4. Scroll through results

### Refining Searches

1. Clear previous results with `Ctrl+C`
2. Modify search parameters
3. Execute new search with `Ctrl+S`

## Search Indices

Available in the Search Index dropdown:

- **Title** (default) - Search book/article titles
- **Author** - Search by author name
- **Subject** - Search by subject headings
- **ISBN** - Search by ISBN number
- **ISSN** - Search by ISSN number
- **Keyword** - Full-text keyword search
- **All Fields** - Search across all metadata
- **Publisher** - Search by publisher name
- **Year** - Search by publication year

## Record Formats

Available output formats:

- **MARCXML** (default) - Standard bibliographic format
- **TurboMARC** - Optimized MARC XML
- **MODS** - Metadata Object Description Schema
- **PICA XML** - PICA format
- **Dublin Core** - Simple metadata format

## Features

### Real-Time Search

Results appear immediately after the search completes, with a loading indicator during processing.

### Formatted Output

Results are displayed in an easy-to-read format with:

- Clear field labels
- Proper spacing
- Consistent formatting
- Scrollable container for many results

### Error Handling

The TUI provides helpful error messages:

- Connection errors with suggestions
- No results found notifications
- Invalid query syntax warnings
- Server error explanations

## Advanced Usage

### CQL Queries

Enter complex queries directly in the Query field:

```
pica.tit="Python" and pica.per="Guido"
```

```
pica.tit="Machine Learning" and pica.ejr=2023
```

### Wildcard Searches

Use wildcards in your queries:

```
Pytho*
```

```
*learning*
```

## Limitations

!!! warning "Current Limitations"
    The experimental TUI currently has some limitations:

    - No library holdings display (use CLI for holdings)
    - No profile switching (uses default SWB catalog)
    - No result export functionality
    - Limited to 100 records per search

    These features may be added in future versions.

## Tips & Tricks

### Fast Searching

1. Use keyboard shortcuts exclusively
2. Keep common searches in clipboard
3. Use wildcards liberally
4. Start with broad terms, refine as needed

### Efficient Navigation

- `Tab` through all fields quickly
- Use arrow keys in dropdowns instead of mouse
- `Ctrl+C` to reset and start fresh search
- `Ctrl+Q` for quick exit

### Working with Results

- Scroll through results with arrow keys or mouse wheel
- Copy text directly from the terminal
- Take note of ISBNs for CLI commands with holdings

## Troubleshooting

### TUI Won't Start

If the TUI fails to launch:

```bash
# Check if textual is installed
python -c "import textual; print(textual.__version__)"

# Reinstall if missing
uv pip install textual>=6.12.0
```

### Display Issues

If the TUI looks broken:

- Resize your terminal window (minimum 80x24)
- Try a different terminal emulator
- Check terminal color support

### Slow Performance

If searches are slow:

- Reduce max records setting
- Use more specific search terms
- Check network connection
- Try different search index

## Switching to CLI

For advanced features not available in TUI, use the CLI:

```bash
# Holdings information
swb isbn 978-3-16-148410-0 --holdings

# Different catalog profiles
swb search "Python" --profile k10plus

# Export results
swb search "Python" --output results.txt

# Sorting
swb search "Python" --sort-by year
```

## Future Enhancements

Planned features for future versions:

- [ ] Library holdings display
- [ ] Profile switching in UI
- [ ] Result export functionality
- [ ] Advanced search form
- [ ] Search history
- [ ] Favorites/bookmarks
- [ ] Configurable keyboard shortcuts
- [ ] Theme customization

## Feedback

Found a bug or have a feature request? Please [open an issue](https://github.com/jvanvinkenroye/swb/issues) on GitHub.

## Next Steps

- [CLI Reference](cli.md) - Learn all CLI commands
- [Advanced Features](advanced.md) - CQL queries and more
- [API Reference](../api/overview.md) - Use in your Python code
