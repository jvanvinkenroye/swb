# SWB API Client

A powerful Python CLI client for querying the **Südwestdeutscher Bibliotheksverbund (SWB)** library catalog via the SRU (Search/Retrieve via URL) API.

## Overview

The SWB API Client provides both an interactive terminal UI and a comprehensive command-line interface for searching German library catalogs. Whether you're a researcher, librarian, or developer, this tool makes it easy to discover and access bibliographic information.

## Key Features

### 🖥️ Interactive Terminal UI
- User-friendly terminal interface powered by Textual
- Real-time search with formatted results
- Keyboard shortcuts for efficient navigation
- Perfect for exploring without memorizing commands

### 🔍 Powerful Search Capabilities
- Simple keyword search or advanced CQL queries
- Multiple search indices (title, author, ISBN, ISSN, subject, etc.)
- Sort by relevance, year, author, or title
- Index scanning for auto-completion
- Band/linking search for multi-volume works

### 📚 Multi-Catalog Support
- **6 pre-configured library profiles**: SWB, K10plus, DNB, GBV, BVB, HeBIS
- Switch between catalogs with a single option
- Custom endpoint support

### 📖 Library Holdings
- See which libraries have items
- Access information (online, VPN, campus-only)
- Collection and location details

### 🎯 Developer-Friendly
- Clean Python API for integration
- Multiple output formats (MARCXML, MODS, TurboMARC, etc.)
- Type-safe with full mypy support
- Well-tested (77 tests, 63% coverage)

## Quick Start

```bash
# Install
uv pip install -e .

# Launch interactive UI
swb-tui

# Or use CLI
swb search "Python programming"
swb isbn 978-3-16-148410-0 --holdings
swb search "Goethe" --profile dnb
```

## Why SWB API Client?

- **Easy to Use**: Interactive TUI for beginners, powerful CLI for experts
- **Comprehensive**: Access multiple German library catalogs from one tool
- **Fast**: Efficient queries with smart caching
- **Well-Documented**: Extensive documentation and examples
- **Open Source**: MIT licensed, contributions welcome

## What's Next?

<div class="grid cards" markdown>

-   :material-rocket-launch: **[Installation Guide](user-guide/installation.md)**

    ---

    Get up and running in minutes with our step-by-step installation guide

-   :material-book-open-variant: **[User Guide](user-guide/getting-started.md)**

    ---

    Learn the basics and explore advanced features

-   :material-code-braces: **[API Reference](api/overview.md)**

    ---

    Integrate the SWB client into your Python applications

-   :material-github: **[Development](development/contributing.md)**

    ---

    Contribute to the project and help make it better

</div>

## Requirements

- Python 3.12 or higher
- Internet connection for API access
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## License

This project is licensed under the MIT License. See the [License](about/license.md) page for details.

## Acknowledgments

Special thanks to:

- **Bibliotheksservice-Zentrum Baden-Württemberg (BSZ)** for providing the SRU API
- **K10plus consortium** for the comprehensive library catalog
- The open-source community for the amazing tools that make this project possible
