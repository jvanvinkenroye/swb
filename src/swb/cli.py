"""Command-line interface for the SWB API client."""

import logging
import sys
from pathlib import Path

import click
import requests
from rich import box
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from swb.api import SWBClient
from swb.models import (
    RecordFormat,
    RecordType,
    RelationType,
    SearchIndex,
    SearchResponse,
    SortBy,
    SortOrder,
)
from swb.profiles import PROFILES, get_profile

console = Console()
console_err = Console(stderr=True)


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging with Rich handler.

    Args:
        verbose: Enable debug logging.
        quiet: Suppress all logging except errors.
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def display_results(
    response: SearchResponse,
    show_raw: bool = False,
    output_file: Path | None = None,
    show_holdings: bool = False,
) -> None:
    """Display search results in a formatted table.

    Args:
        response: Search response containing results.
        show_raw: Whether to display raw XML data.
        output_file: Optional file path to save results.
        show_holdings: Whether to display library holdings information.
    """
    if response.total_results == 0:
        console.print("[yellow]No results found.[/yellow]")
        return

    # Create summary panel
    summary = Text()
    summary.append("Found ", style="bold")
    summary.append(f"{response.total_results}", style="bold cyan")
    summary.append(" result(s)\n", style="bold")
    summary.append(f"Showing {len(response.results)} record(s)")

    console.print(Panel(summary, title="Search Results", border_style="blue"))
    console.print()

    # Create results table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", style="cyan", no_wrap=False)
    table.add_column("Author", style="green")
    table.add_column("Year", style="yellow", width=6)
    table.add_column("ISBN", style="blue")

    output_lines = []

    for idx, result in enumerate(response.results, 1):
        table.add_row(
            str(idx),
            result.title or "N/A",
            result.author or "N/A",
            result.year or "N/A",
            result.isbn or "N/A",
        )

        # Prepare output for file
        if output_file:
            output_lines.append(f"\n{'=' * 80}")
            output_lines.append(f"Record {idx}")
            output_lines.append(f"{'=' * 80}")
            output_lines.append(f"Title: {result.title or 'N/A'}")
            output_lines.append(f"Author: {result.author or 'N/A'}")
            output_lines.append(f"Year: {result.year or 'N/A'}")
            output_lines.append(f"Publisher: {result.publisher or 'N/A'}")
            output_lines.append(f"ISBN: {result.isbn or 'N/A'}")
            output_lines.append(f"Record ID: {result.record_id or 'N/A'}")

            if show_holdings and result.holdings:
                output_lines.append("\nLibrary Holdings:")
                for holding in result.holdings:
                    output_lines.append(
                        f"\n  Library: {holding.library_name or holding.library_code}"
                    )
                    if holding.collection:
                        output_lines.append(f"  Collection: {holding.collection}")
                    if holding.access_url:
                        output_lines.append(f"  Access URL: {holding.access_url}")
                    if holding.access_note:
                        output_lines.append(f"  Access Note: {holding.access_note}")

            if show_raw and result.raw_data:
                output_lines.append(f"\nRaw Data:\n{result.raw_data}")

    console.print(table)
    console.print()

    # Display raw data if requested
    if show_raw and not output_file:
        for idx, result in enumerate(response.results, 1):
            console.print(f"\n[bold]Record {idx} - Raw Data:[/bold]")
            if result.raw_data:
                console.print(Panel(result.raw_data, border_style="dim"))

    # Display holdings if requested
    if show_holdings and not output_file:
        for idx, result in enumerate(response.results, 1):
            if result.holdings:
                console.print(f"\n[bold]Record {idx} - Library Holdings:[/bold]")
                holdings_table = Table(
                    show_header=True, header_style="bold cyan", box=box.ROUNDED
                )
                holdings_table.add_column("Library", style="green", no_wrap=False)
                holdings_table.add_column("Collection", style="yellow")
                holdings_table.add_column("Access", style="blue", no_wrap=False)

                for holding in result.holdings:
                    # Improved library display with better fallback handling
                    if (
                        holding.library_name
                        and holding.library_name != holding.library_code
                    ):
                        library_display = (
                            f"{holding.library_name} ({holding.library_code})"
                        )
                    elif holding.library_name:
                        library_display = holding.library_name
                    elif holding.library_code:
                        # Try to make unknown codes more readable
                        if holding.library_code.startswith("DE-"):
                            suffix = holding.library_code[3:]
                            if suffix.isdigit():
                                library_display = f"German Library DE-{suffix}"
                            else:
                                library_display = (
                                    f"German Library {holding.library_code}"
                                )
                        else:
                            library_display = f"Library {holding.library_code}"
                    else:
                        library_display = "Unknown Library"

                    access_info = []
                    if holding.access_url:
                        access_info.append(
                            f"[link={holding.access_url}]Online Access[/link]"
                        )
                    if holding.access_note:
                        access_info.append(holding.access_note)
                    access_display = "\n".join(access_info) if access_info else "N/A"

                    holdings_table.add_row(
                        library_display,
                        holding.collection or "N/A",
                        access_display,
                    )

                console.print(holdings_table)
            else:
                console.print(
                    f"\n[dim]Record {idx} - No holdings information available[/dim]"
                )

    # Show pagination info
    if response.has_more:
        console.print(
            f"[dim]More results available. Use --start-record {response.next_record} "
            f"to see next page.[/dim]"
        )

    # Save to file if requested
    if output_file:
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text("\n".join(output_lines))
            console.print(f"[green]Results saved to {output_file}[/green]")
        except OSError as e:
            console.print(f"[red]Failed to save results: {e}[/red]")


def resolve_base_url(profile: str | None, url: str | None) -> str:
    """Resolve the base URL from profile or custom URL.

    Args:
        profile: Profile name (e.g., 'swb', 'k10plus', 'dnb')
        url: Custom SRU endpoint URL

    Returns:
        Base URL to use for the SWB client

    Raises:
        ValueError: If profile is unknown
    """
    if url:
        # Custom URL takes precedence
        return url
    if profile:
        # Resolve profile to URL
        catalog_profile = get_profile(profile)
        return catalog_profile.url
    # Use default profile if neither provided
    return get_profile("swb").url


def handle_api_error(e: Exception, base_url: str) -> None:
    """Handle API errors and provide user-friendly messages.

    Args:
        e: Exception that was raised
        base_url: URL that was being accessed
    """
    if isinstance(e, requests.HTTPError):
        if e.response and e.response.status_code == 403:
            console_err.print("[red]Access Denied (403 Forbidden)[/red]")
            console_err.print(f"[bold]Server:[/bold] {base_url}")
            console_err.print()
            console_err.print("[bold]Possible Solutions:[/bold]")
            console_err.print(
                "- Try a different catalog profile: --profile k10plus, dnb, gvk, etc."
            )
            console_err.print("- Check if the server requires authentication (API key)")
            console_err.print("- Try using a VPN or different network connection")
            console_err.print(
                "- The server may be temporarily unavailable or have changed policies"
            )
            console_err.print()
            console_err.print("[bold]Available profiles:[/bold]")
            for profile_name in PROFILES.keys():
                console_err.print(f"  - {profile_name}")
            console_err.print()
            console_err.print("[bold]Example:[/bold]")
            console_err.print("  swb search 'Python' --profile k10plus")
            console_err.print("  swb search 'Python' --profile dnb")
        else:
            console_err.print(
                f"[red]HTTP Error {e.response.status_code if e.response else 'Unknown'}:[/red] {e}"
            )
    else:
        console_err.print(f"[red]Error:[/red] {e}")


@click.group()
@click.version_option(version="0.1.0")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose logging (DEBUG level).",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Suppress all output except errors.",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """SWB API Client - Search the Südwestdeutscher Bibliotheksverbund catalog.

    This tool provides a command-line interface to query the SWB library catalog
    using the SRU (Search/Retrieve via URL) protocol.

    Examples:

        Search for books about Python:

            swb search "Python" --index title

        Search by ISBN:

            swb isbn 978-3-16-148410-0

        Get detailed results in MODS format:

            swb search "Machine Learning" --format mods --max 20
    """
    setup_logging(verbose, quiet)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


@cli.command()
@click.argument("query")
@click.option(
    "--index",
    "-i",
    type=click.Choice(
        [index.name.lower() for index in SearchIndex],
        case_sensitive=False,
    ),
    help="Search index to use (e.g., title, author, isbn).",
)
@click.option(
    "--format",
    "-f",
    "record_format",
    type=click.Choice(
        [fmt.name.lower() for fmt in RecordFormat],
        case_sensitive=False,
    ),
    default="marcxml",
    help="Record format for results.",
)
@click.option(
    "--max",
    "-m",
    "maximum_records",
    type=int,
    default=10,
    help="Maximum number of records to retrieve.",
)
@click.option(
    "--start-record",
    "-s",
    type=int,
    default=1,
    help="Starting record position (for pagination).",
)
@click.option(
    "--raw",
    is_flag=True,
    help="Display raw XML data.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save results to file.",
)
@click.option(
    "--profile",
    "-p",
    type=click.Choice(list(PROFILES.keys()), case_sensitive=False),
    help="Library catalog profile (swb, k10plus, gvk, dnb, bvb, hebis).",
)
@click.option(
    "--url",
    type=str,
    help="Custom SRU endpoint URL (overrides --profile).",
)
@click.option(
    "--sort-by",
    type=click.Choice(["relevance", "year", "author", "title"], case_sensitive=False),
    help="Sort results by relevance, year, author, or title.",
)
@click.option(
    "--sort-order",
    type=click.Choice(["ascending", "descending"], case_sensitive=False),
    default="descending",
    help="Sort order (ascending or descending).",
)
@click.option(
    "--packing",
    type=click.Choice(["xml", "string"], case_sensitive=False),
    default="xml",
    help="Record packing mode (xml or string).",
)
@click.option(
    "--holdings",
    is_flag=True,
    help="Display library holdings information.",
)
@click.pass_context
def search(
    ctx: click.Context,
    query: str,
    index: str | None,
    record_format: str,
    maximum_records: int,
    start_record: int,
    raw: bool,
    output: Path | None,
    profile: str | None,
    url: str | None,
    sort_by: str | None,
    sort_order: str,
    packing: str,
    holdings: bool,
) -> None:
    """Search the SWB catalog.

    QUERY can be a simple keyword or a full CQL query string.

    Examples:

        swb search "Python programming"

        swb search "Goethe" --index author --max 20

        swb search 'pica.tit="Faust" and pica.per="Goethe"'
    """
    try:
        # Convert string arguments to enums
        search_index = SearchIndex[index.upper()] if index else None
        fmt = RecordFormat[record_format.upper()]
        sort_by_enum = SortBy[sort_by.upper()] if sort_by else None
        sort_order_enum = SortOrder[sort_order.upper()]

        base_url = resolve_base_url(profile, url)
        with SWBClient(base_url=base_url) as client:
            if not ctx.obj.get("quiet"):
                console.print(f"[bold]Searching for:[/bold] {query}")
                if search_index:
                    console.print(f"[bold]Index:[/bold] {search_index.name}")
                if sort_by_enum:
                    console.print(
                        f"[bold]Sort:[/bold] {sort_by_enum.name} ({sort_order_enum.name})"
                    )
                console.print()

            response = client.search(
                query=query,
                index=search_index,
                record_format=fmt,
                start_record=start_record,
                maximum_records=maximum_records,
                sort_by=sort_by_enum,
                sort_order=sort_order_enum,
                record_packing=packing,
            )

            display_results(
                response, show_raw=raw, output_file=output, show_holdings=holdings
            )

    except Exception as e:
        handle_api_error(e, base_url)
        logging.exception("Search failed")
        sys.exit(1)


@cli.command()
@click.argument("isbn")
@click.option(
    "--format",
    "-f",
    "record_format",
    type=click.Choice(
        [fmt.name.lower() for fmt in RecordFormat],
        case_sensitive=False,
    ),
    default="marcxml",
    help="Record format for results.",
)
@click.option(
    "--raw",
    is_flag=True,
    help="Display raw XML data.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save results to file.",
)
@click.option(
    "--profile",
    "-p",
    type=click.Choice(list(PROFILES.keys()), case_sensitive=False),
    help="Library catalog profile (swb, k10plus, gvk, dnb, bvb, hebis).",
)
@click.option(
    "--url",
    type=str,
    help="Custom SRU endpoint URL (overrides --profile).",
)
@click.option(
    "--packing",
    type=click.Choice(["xml", "string"], case_sensitive=False),
    default="xml",
    help="Record packing mode (xml or string).",
)
@click.option(
    "--holdings",
    is_flag=True,
    help="Display library holdings information.",
)
@click.pass_context
def isbn(
    ctx: click.Context,
    isbn: str,
    record_format: str,
    raw: bool,
    output: Path | None,
    profile: str | None,
    url: str | None,
    packing: str,
    holdings: bool,
) -> None:
    """Search for a book by ISBN number.

    ISBN can include hyphens or spaces, which will be automatically removed.

    Examples:

        swb isbn 978-3-16-148410-0

        swb isbn 9783161484100 --format mods
    """
    try:
        fmt = RecordFormat[record_format.upper()]

        base_url = resolve_base_url(profile, url)
        with SWBClient(base_url=base_url) as client:
            if not ctx.obj.get("quiet"):
                console.print(f"[bold]Searching for ISBN:[/bold] {isbn}")
                console.print()

            response = client.search_by_isbn(
                isbn, record_format=fmt, record_packing=packing
            )
            display_results(
                response, show_raw=raw, output_file=output, show_holdings=holdings
            )

    except Exception as e:
        handle_api_error(e, base_url)
        logging.exception("ISBN search failed")
        sys.exit(1)


@cli.command()
@click.argument("issn")
@click.option(
    "--format",
    "-f",
    "record_format",
    type=click.Choice(
        [fmt.name.lower() for fmt in RecordFormat],
        case_sensitive=False,
    ),
    default="marcxml",
    help="Record format for results.",
)
@click.option(
    "--raw",
    is_flag=True,
    help="Display raw XML data.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save results to file.",
)
@click.option(
    "--profile",
    "-p",
    type=click.Choice(list(PROFILES.keys()), case_sensitive=False),
    help="Library catalog profile (swb, k10plus, gvk, dnb, bvb, hebis).",
)
@click.option(
    "--url",
    type=str,
    help="Custom SRU endpoint URL (overrides --profile).",
)
@click.option(
    "--packing",
    type=click.Choice(["xml", "string"], case_sensitive=False),
    default="xml",
    help="Record packing mode (xml or string).",
)
@click.option(
    "--holdings",
    is_flag=True,
    help="Display library holdings information.",
)
@click.pass_context
def issn(
    ctx: click.Context,
    issn: str,
    record_format: str,
    raw: bool,
    output: Path | None,
    profile: str | None,
    url: str | None,
    packing: str,
    holdings: bool,
) -> None:
    """Search for a periodical by ISSN number.

    ISSN can include hyphens, which will be automatically removed.

    Examples:

        swb issn 0028-0836

        swb issn 00280836 --format mods
    """
    try:
        fmt = RecordFormat[record_format.upper()]

        base_url = resolve_base_url(profile, url)
        with SWBClient(base_url=base_url) as client:
            if not ctx.obj.get("quiet"):
                console.print(f"[bold]Searching for ISSN:[/bold] {issn}")
                console.print()

            response = client.search_by_issn(
                issn, record_format=fmt, record_packing=packing
            )
            display_results(
                response, show_raw=raw, output_file=output, show_holdings=holdings
            )

    except Exception as e:
        handle_api_error(e, base_url)
        logging.exception("ISSN search failed")
        sys.exit(1)


@cli.command()
@click.argument("ppn")
@click.option(
    "--relation-type",
    "-r",
    type=click.Choice(
        [rel.name.lower() for rel in RelationType],
        case_sensitive=False,
    ),
    required=True,
    help="Type of relationship (family, parent, child, related, thesaurus).",
)
@click.option(
    "--record-type",
    "-t",
    type=click.Choice(
        [rec.name.lower() for rec in RecordType],
        case_sensitive=False,
    ),
    default="bibliographic",
    help="Type of records to retrieve (bibliographic or authority).",
)
@click.option(
    "--format",
    "-f",
    "record_format",
    type=click.Choice(
        [fmt.name.lower() for fmt in RecordFormat],
        case_sensitive=False,
    ),
    default="marcxml",
    help="Record format for results.",
)
@click.option(
    "--max",
    "-m",
    "maximum_records",
    type=int,
    default=10,
    help="Maximum number of records to retrieve.",
)
@click.option(
    "--start-record",
    "-s",
    type=int,
    default=1,
    help="Starting record position (for pagination).",
)
@click.option(
    "--raw",
    is_flag=True,
    help="Display raw XML data.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save results to file.",
)
@click.option(
    "--profile",
    "-p",
    type=click.Choice(list(PROFILES.keys()), case_sensitive=False),
    help="Library catalog profile (swb, k10plus, gvk, dnb, bvb, hebis).",
)
@click.option(
    "--url",
    type=str,
    help="Custom SRU endpoint URL (overrides --profile).",
)
@click.option(
    "--sort-by",
    type=click.Choice(["relevance", "year", "author", "title"], case_sensitive=False),
    help="Sort results by relevance, year, author, or title.",
)
@click.option(
    "--sort-order",
    type=click.Choice(["ascending", "descending"], case_sensitive=False),
    default="descending",
    help="Sort order (ascending or descending).",
)
@click.option(
    "--packing",
    type=click.Choice(["xml", "string"], case_sensitive=False),
    default="xml",
    help="Record packing mode (xml or string).",
)
@click.option(
    "--holdings",
    is_flag=True,
    help="Display library holdings information.",
)
@click.pass_context
def related(
    ctx: click.Context,
    ppn: str,
    relation_type: str,
    record_type: str,
    record_format: str,
    maximum_records: int,
    start_record: int,
    raw: bool,
    output: Path | None,
    profile: str | None,
    url: str | None,
    sort_by: str | None,
    sort_order: str,
    packing: str,
    holdings: bool,
) -> None:
    """Search for records related to a specific publication (band/linking search).

    PPN is the PICA Production Number of the parent record.

    This command is useful for finding related publications in multi-volume works,
    series, or hierarchical bibliographic relationships.

    Examples:

        Find all volumes (child records) of a multi-volume work:

            swb related 267838395 --relation-type child

        Find the parent record of a volume:

            swb related 123456789 --relation-type parent

        Find entire family of related records:

            swb related 267838395 --relation-type family --max 50
    """
    try:
        # Convert string arguments to enums
        relation_type_enum = RelationType[relation_type.upper()]
        record_type_enum = RecordType[record_type.upper()]
        fmt = RecordFormat[record_format.upper()]
        sort_by_enum = SortBy[sort_by.upper()] if sort_by else None
        sort_order_enum = SortOrder[sort_order.upper()]

        base_url = resolve_base_url(profile, url)
        with SWBClient(base_url=base_url) as client:
            if not ctx.obj.get("quiet"):
                console.print(
                    f"[bold]Searching for records related to PPN:[/bold] {ppn}"
                )
                console.print(f"[bold]Relation Type:[/bold] {relation_type_enum.name}")
                console.print(f"[bold]Record Type:[/bold] {record_type_enum.name}")
                if sort_by_enum:
                    console.print(
                        f"[bold]Sort:[/bold] {sort_by_enum.name} ({sort_order_enum.name})"
                    )
                console.print()

            response = client.search_related(
                ppn=ppn,
                relation_type=relation_type_enum,
                record_type=record_type_enum,
                record_format=fmt,
                start_record=start_record,
                maximum_records=maximum_records,
                sort_by=sort_by_enum,
                sort_order=sort_order_enum,
                record_packing=packing,
            )

            display_results(
                response, show_raw=raw, output_file=output, show_holdings=holdings
            )

    except Exception as e:
        handle_api_error(e, base_url)
        logging.exception("Related records search failed")
        sys.exit(1)


@cli.command()
def formats() -> None:
    """List available record formats."""
    table = Table(title="Available Record Formats", show_header=True)
    table.add_column("Format", style="cyan")
    table.add_column("Value", style="green")

    for fmt in RecordFormat:
        table.add_row(fmt.name, fmt.value)

    console.print(table)


@cli.command()
def indices() -> None:
    """List available search indices."""
    table = Table(title="Available Search Indices", show_header=True)
    table.add_column("Index", style="cyan")
    table.add_column("CQL Name", style="green")

    for index in SearchIndex:
        table.add_row(index.name, index.value)

    console.print(table)


@cli.command()
def profiles() -> None:
    """List available library catalog profiles."""
    from swb.profiles import list_profiles

    table = Table(title="Available Library Catalog Profiles", show_header=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Display Name", style="green")
    table.add_column("Region", style="yellow")
    table.add_column("Description", style="white")

    for profile in list_profiles():
        table.add_row(
            profile.name,
            profile.display_name,
            profile.region,
            profile.description,
        )

    console.print(table)
    console.print('\n[dim]Use with: swb search "query" --profile <name>[/dim]')


@cli.command()
@click.argument("scan_clause")
@click.option(
    "--max",
    "-m",
    "maximum_terms",
    type=int,
    default=20,
    help="Maximum number of terms to retrieve.",
)
@click.option(
    "--position",
    "response_position",
    type=int,
    default=1,
    help="Starting position in the term list.",
)
@click.option(
    "--profile",
    "-p",
    type=click.Choice(list(PROFILES.keys()), case_sensitive=False),
    help="Library catalog profile (swb, k10plus, gvk, dnb, bvb, hebis).",
)
@click.option(
    "--url",
    type=str,
    help="Custom SRU endpoint URL (overrides --profile).",
)
@click.pass_context
def scan(
    ctx: click.Context,
    scan_clause: str,
    maximum_terms: int,
    response_position: int,
    profile: str | None,
    url: str | None,
) -> None:
    """Scan an index for terms (auto-completion and browsing).

    SCAN_CLAUSE is a CQL scan clause to browse index terms.

    Examples:

        Find authors starting with "Goe":

            swb scan "pica.per=Goe"

        Find titles starting with "Python":

            swb scan "pica.tit=Python" --max 10

        Browse subjects:

            swb scan "pica.sub=Machine Learning"
    """
    try:
        base_url = resolve_base_url(profile, url)
        with SWBClient(base_url=base_url) as client:
            if not ctx.obj.get("quiet"):
                console.print(f"[bold]Scanning:[/bold] {scan_clause}")
                console.print()

            response = client.scan(
                scan_clause=scan_clause,
                response_position=response_position,
                maximum_terms=maximum_terms,
            )

            # Display results in a table
            if not response.terms:
                console.print("[yellow]No terms found.[/yellow]")
                return

            table = Table(title="Scan Results", show_header=True)
            table.add_column("#", style="dim", width=4)
            table.add_column("Term", style="cyan", no_wrap=False)
            table.add_column("Records", style="green", justify="right")

            for idx, term in enumerate(response.terms, 1):
                display_value = term.display_term or term.value
                table.add_row(
                    str(idx),
                    display_value,
                    str(term.number_of_records),
                )

            console.print(table)
            console.print()
            console.print(f"[dim]Found {len(response.terms)} terms[/dim]")

    except Exception as e:
        handle_api_error(e, base_url)
        logging.exception("Scan failed")
        sys.exit(1)


@cli.command()
@click.option(
    "--profile",
    "-p",
    type=click.Choice(list(PROFILES.keys()), case_sensitive=False),
    help="Library catalog profile (swb, k10plus, gvk, dnb, bvb, hebis).",
)
@click.option(
    "--url",
    type=str,
    help="Custom SRU endpoint URL (overrides --profile).",
)
@click.pass_context
def explain(
    ctx: click.Context,
    profile: str | None,
    url: str | None,
) -> None:
    """Display server capabilities and configuration.

    The explain operation retrieves information about the SRU server including:
    - Server and database information
    - Available search indices
    - Supported record formats

    Example:

        swb explain
    """
    try:
        base_url = resolve_base_url(profile, url)
        with SWBClient(base_url=base_url) as client:
            if not ctx.obj.get("quiet"):
                console.print("[bold]Fetching server information...[/bold]")
                console.print()

            response = client.explain()

            # Display server info
            console.print("[bold cyan]Server Information[/bold cyan]")
            table = Table(show_header=False, box=None)
            table.add_column("Key", style="green")
            table.add_column("Value", style="white")
            table.add_row("Host", response.server_info.host)
            if response.server_info.port:
                table.add_row("Port", str(response.server_info.port))
            if response.server_info.database:
                table.add_row("Database", response.server_info.database)
            console.print(table)
            console.print()

            # Display database info
            console.print("[bold cyan]Database Information[/bold cyan]")
            table = Table(show_header=False, box=None)
            table.add_column("Key", style="green")
            table.add_column("Value", style="white")
            table.add_row("Title", response.database_info.title)
            if response.database_info.description:
                table.add_row(
                    "Description",
                    response.database_info.description[:100] + "..."
                    if len(response.database_info.description) > 100
                    else response.database_info.description,
                )
            console.print(table)
            console.print()

            # Display supported schemas
            console.print(
                f"[bold cyan]Supported Record Formats[/bold cyan] ({len(response.schemas)})"
            )
            schema_table = Table(show_header=True, header_style="bold magenta")
            schema_table.add_column("Identifier", style="cyan")
            schema_table.add_column("Name", style="green")

            for schema in response.schemas:
                schema_table.add_row(schema.identifier, schema.name)

            console.print(schema_table)
            console.print()

            # Display available indices (first 20 only)
            console.print(
                f"[bold cyan]Available Search Indices[/bold cyan] "
                f"({len(response.indices)} total, showing first 20)"
            )
            index_table = Table(show_header=True, header_style="bold magenta")
            index_table.add_column("#", style="dim", width=4)
            index_table.add_column("CQL Name", style="cyan", no_wrap=False)
            index_table.add_column("Title", style="green", no_wrap=False)

            for idx, index in enumerate(response.indices[:20], 1):
                index_table.add_row(
                    str(idx),
                    index.name,
                    index.title,
                )

            console.print(index_table)

            if len(response.indices) > 20:
                console.print(
                    f"\n[dim]... and {len(response.indices) - 20} more indices[/dim]"
                )

    except Exception as e:
        handle_api_error(e, base_url)
        logging.exception("Explain operation failed")
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI application."""
    cli(obj={})


if __name__ == "__main__":
    main()
