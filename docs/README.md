# Documentation

This directory contains the MkDocs documentation for the SWB API Client.

## Building the Documentation

Install documentation dependencies:

```bash
uv pip install mkdocs mkdocs-material "mkdocstrings[python]" pymdown-extensions
```

Build the documentation:

```bash
# Using uv (recommended)
uv run mkdocs build

# Or directly
mkdocs build
```

## Serving Locally

Serve the documentation locally with live reload:

```bash
# Using uv
uv run mkdocs serve

# Or directly
mkdocs serve
```

Then open http://127.0.0.1:8000 in your browser.

## Structure

- `index.md` - Homepage
- `user-guide/` - User documentation
  - `installation.md` - Installation instructions
  - `getting-started.md` - Basic usage
  - `tui.md` - Terminal UI guide
  - `cli.md` - CLI reference
  - `profiles.md` - Catalog profiles
  - `advanced.md` - Advanced features
- `api/` - API reference
  - `overview.md` - API overview
  - `client.md` - SWBClient reference
  - `models.md` - Data models
  - `profiles.md` - Profiles API
- `development/` - Development guides
  - `contributing.md` - Contributing guide
  - `testing.md` - Testing guide
  - `code-quality.md` - Code quality tools
- `about/` - About and resources
  - `resources.md` - Links and resources
  - `license.md` - License information

## Publishing

The documentation is automatically built and published to GitHub Pages on push to main.

To publish manually:

```bash
uv run mkdocs gh-deploy
```

## Configuration

Documentation configuration is in `mkdocs.yml` at the project root.
