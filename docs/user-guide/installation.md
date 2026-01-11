# Installation

This guide will help you install the SWB API Client on your system.

## Prerequisites

Before installing, make sure you have:

- **Python 3.12 or higher** installed
- **Internet connection** for API access
- **uv** (recommended) or pip package manager

## Installing uv

We recommend using [uv](https://github.com/astral-sh/uv) for fast and reliable package management.

=== "macOS/Linux"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows"

    ```powershell
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

=== "With pip"

    ```bash
    pip install uv
    ```

## Installing SWB Client

### From Source (Recommended)

Clone the repository and install in development mode:

```bash
# Clone the repository
git clone https://github.com/jvanvinkenroye/swb.git
cd swb

# Create virtual environment
uv venv --seed

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Install the package
uv pip install -e .
```

!!! tip "Development Installation"
    The `-e` flag installs the package in editable mode, which means changes to the source code will be immediately available without reinstalling.

### With Development Dependencies

If you plan to contribute or run tests:

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Or sync all dependencies
uv sync --dev
```

## Verifying Installation

After installation, verify that everything works:

```bash
# Check CLI version
swb --version

# Test a simple search
swb search "Python" --max 5

# Launch the TUI
swb-tui
```

You should see the version number and search results if everything is installed correctly.

## Optional: Shell Completion

### Bash

Add to `~/.bashrc`:

```bash
eval "$(_SWB_COMPLETE=bash_source swb)"
```

### Zsh

Add to `~/.zshrc`:

```bash
eval "$(_SWB_COMPLETE=zsh_source swb)"
```

### Fish

Add to `~/.config/fish/completions/swb.fish`:

```fish
eval (env _SWB_COMPLETE=fish_source swb)
```

## Troubleshooting

### SSL Certificate Errors

If you encounter SSL certificate errors:

=== "macOS"

    ```bash
    brew install ca-certificates
    ```

=== "Ubuntu/Debian"

    ```bash
    sudo apt-get update
    sudo apt-get install ca-certificates
    ```

=== "Windows"

    Update your certificates via Windows Update or download from [certifi.io](https://certifi.io/)

### Permission Errors

If you get permission errors during installation:

```bash
# Don't use sudo with uv - use virtual environments instead
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Python Version Issues

Make sure you're using Python 3.12 or higher:

```bash
python --version
# or
python3 --version
```

If you need to install Python 3.12:

=== "macOS"

    ```bash
    brew install python@3.12
    ```

=== "Ubuntu/Debian"

    ```bash
    sudo apt-get install python3.12
    ```

=== "Windows"

    Download from [python.org](https://www.python.org/downloads/)

## Updating

To update to the latest version:

```bash
cd swb
git pull
uv pip install -e .
```

## Uninstalling

To remove the SWB client:

```bash
uv pip uninstall swb
```

## Next Steps

Now that you have the SWB client installed, check out:

- [Getting Started](getting-started.md) - Learn the basics
- [Terminal UI Guide](tui.md) - Explore the interactive interface
- [CLI Reference](cli.md) - Master the command line
