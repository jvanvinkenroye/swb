"""Direct Textual TUI for the SWB API Client (simplified version)."""

from __future__ import annotations

import logging
import os
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    LoadingIndicator,
    Markdown,
    Select,
    Static,
)

from swb.api import SWBClient
from swb.models import (
    RecordFormat,
    SearchIndex,
    SearchResult,
)

logger = logging.getLogger(__name__)


class SWBTUIDirect(App[None]):
    """Direct Textual TUI application for SWB API Client."""

    CSS = """
    Screen {
        align: center middle;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    #main-container {
        width: 100%;
        max-width: 120;
        margin: 1 2;
    }

    #search-form {
        padding: 1;
        border: round $primary;
        margin-bottom: 1;
    }

    #results-container {
        height: 40;
        border: round $secondary;
        padding: 1;
        margin-top: 1;
        overflow-y: auto;
    }

    #loading-indicator {
        dock: top;
    }

    .error {
        color: $error;
        text-style: bold;
    }

    Input, Select, Button {
        width: 100%;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+s", "search", "Search", show=True),
        Binding("ctrl+c", "clear", "Clear", show=True),
    ]

    # Reactive variables
    search_query = reactive("")
    search_index = reactive("title")
    record_format = reactive("marcxml")
    max_records = reactive("10")
    is_searching = reactive(False)
    search_results: reactive[list[SearchResult]] = reactive([])
    error_message = reactive("")

    def compose(self) -> ComposeResult:
        """Compose the application UI."""
        yield Header(show_clock=True)

        with Container(id="main-container"):
            # Search form
            with Container(id="search-form"):
                yield Label("SWB Catalog Search", id="title")
                yield Input(placeholder="Enter search query...", id="query-input")

                # Options
                yield Label("Search Index:", id="index-label")
                yield Select(
                    [(index.name.lower(), index.name) for index in SearchIndex],
                    value="TITLE",
                    allow_blank=False,
                    id="index-select",
                )

                yield Label("Record Format:", id="format-label")
                yield Select(
                    [(fmt.name.lower(), fmt.name) for fmt in RecordFormat],
                    value="MARCXML",
                    allow_blank=False,
                    id="format-select",
                )

                yield Label("Max Records:", id="max-label")
                yield Input(placeholder="Max records", value="10", id="max-input")

                yield Button("Search", id="search-button", variant="primary")
                yield Button("Clear", id="clear-button")

            # Results area
            with ScrollableContainer(id="results-container"):
                yield Static(id="results-area")
                yield LoadingIndicator(id="loading-indicator")
                yield Static(id="error-area", classes="error")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the application."""
        self.title = "SWB API Client TUI"
        self.sub_title = "Search German Library Catalogs"

        # Set up reactive bindings
        query_input = self.query_one("#query-input", Input)
        index_select = self.query_one("#index-select", Select)
        format_select = self.query_one("#format-select", Select)
        max_input = self.query_one("#max-input", Input)

        # Bind reactive variables to widgets
        self.search_query = query_input.value
        self.search_index = str(index_select.value).lower()
        self.record_format = str(format_select.value).lower()
        self.max_records = max_input.value

        # Watch for changes
        self.watch(query_input, "value", self.on_query_change)
        self.watch(index_select, "value", self.on_index_change)
        self.watch(format_select, "value", self.on_format_change)
        self.watch(max_input, "value", self.on_max_change)

        # Hide loading indicator initially
        self.query_one("#loading-indicator").visible = False
        self.query_one("#error-area").visible = False

        # Add initial instructions
        results_area = self.query_one("#results-area", Static)
        results_area.update("🔍 Enter search query and press Search (or Ctrl+S)")

    def on_query_change(self, value: str) -> None:
        """Handle query input changes."""
        self.search_query = value
        logger.info(f"Query changed to: {value}")

    def on_index_change(self, value: str) -> None:
        """Handle search index changes."""
        self.search_index = value.lower()

    def on_format_change(self, value: str) -> None:
        """Handle record format changes."""
        self.record_format = value.lower()

    def on_max_change(self, value: str) -> None:
        """Handle max records changes."""
        self.max_records = value

    @on(Input.Submitted, "#query-input")
    @on(Button.Pressed, "#search-button")
    def perform_search(self) -> None:
        """Perform the search operation."""
        self.action_search()

    @on(Button.Pressed, "#clear-button")
    def clear_results(self) -> None:
        """Clear search results."""
        self.action_clear()

    def action_search(self) -> None:
        """Execute the search action."""
        logger.info(f"Search button pressed with query: '{self.search_query}'")
        if not self.search_query.strip():
            logger.warning("Empty query submitted")
            self.error_message = "Please enter a search query"
            self._show_error()
            return

        # Validate max records
        try:
            max_recs = int(self.max_records)
            if max_recs <= 0 or max_recs > 100:
                self.error_message = "Max records must be between 1 and 100"
                self._show_error()
                return
        except ValueError:
            self.error_message = "Max records must be a valid number"
            self._show_error()
            return

        # Start search
        self.is_searching = True
        self.error_message = ""

        # Show loading indicator
        loading = self.query_one("#loading-indicator", LoadingIndicator)
        results_area = self.query_one("#results-area", Static)
        error_area = self.query_one("#error-area", Static)

        loading.visible = True
        results_area.update("")
        error_area.visible = False

        # Perform search in background
        self.run_worker(self._execute_search)

    async def _execute_search(self) -> None:
        """Execute the search in a background worker."""
        logger.info("Starting search worker execution")
        try:
            with SWBClient() as client:
                response = client.search(
                    query=self.search_query,
                    index=SearchIndex[self.search_index.upper()],
                    record_format=RecordFormat[self.record_format.upper()],
                    maximum_records=int(self.max_records),
                )

                self.search_results = response.results
                self.error_message = ""

        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.error_message = f"Search failed: {e}"
            self.search_results = []

        finally:
            self.is_searching = False
            # Force update to trigger reactive changes
            self.refresh()

            # Directly call display results as fallback
            logger.info("Worker completed, calling _display_results() directly")
            self._display_results()

    def on_worker_state_changed(self, event: Any) -> None:
        """Handle worker state changes."""
        logger.info(f"Worker state changed: {event.state}")

        if event.state == "SUCCESS":
            logger.info(f"Worker completed successfully, results count: {len(self.search_results)}")
            logger.info("About to call _display_results()")
            self._display_results()
            logger.info("Completed _display_results() call")
        elif event.state == "ERROR":
            logger.error(f"Worker error: {event.error}")
            self.error_message = f"Search failed: {event.error}"
            self._show_error()

        # Hide loading indicator
        logger.info("Hiding loading indicator")
        self.query_one("#loading-indicator").visible = False

    def _display_results(self) -> None:
        """Display search results."""
        logger.info(f"Displaying {len(self.search_results)} results in UI")
        results_area = self.query_one("#results-area", Static)
        error_area = self.query_one("#error-area", Static)

        if self.error_message:
            logger.warning(f"Displaying error: {self.error_message}")
            self._show_error()
            return

        if not self.search_results:
            logger.info("No results to display")
            results_area.update("No results found.")
            error_area.visible = False
            return

        # Build results display
        logger.debug(f"Building markdown display for {len(self.search_results)} results")
        markdown_text = f"# Search Results\n\nFound {len(self.search_results)} results:\n\n"

        for idx, result in enumerate(self.search_results, 1):
            markdown_text += f"## Result {idx}\n\n"
            markdown_text += f"**Title:** {result.title or 'N/A'}\n\n"
            markdown_text += f"**Author:** {result.author or 'N/A'}\n\n"
            markdown_text += f"**Year:** {result.year or 'N/A'}\n\n"
            markdown_text += f"**Publisher:** {result.publisher or 'N/A'}\n\n"
            markdown_text += f"**ISBN:** {result.isbn or 'N/A'}\n\n"
            markdown_text += f"**Record ID:** {result.record_id or 'N/A'}\n\n"
            markdown_text += "---\n\n"

        results_area.update(Markdown(markdown_text))  # type: ignore
        logger.info("Results displayed successfully in UI")
        error_area.visible = False

        # Ensure results are visible
        logger.info("Ensuring results area is visible and scrolled to top")
        results_area.visible = True
        results_area.scroll_home()  # Scroll to top to ensure results are visible

        # Force UI refresh
        logger.info("Refreshing UI to show results")
        self.refresh()

    def _show_error(self) -> None:
        """Show error message."""
        error_area = self.query_one("#error-area", Static)
        error_area.update(self.error_message)
        error_area.visible = True

    def action_clear(self) -> None:
        """Clear all inputs and results."""
        query_input = self.query_one("#query-input", Input)
        results_area = self.query_one("#results-area", Static)
        error_area = self.query_one("#error-area", Static)

        query_input.value = ""
        results_area.update("")
        error_area.update("")
        error_area.visible = False

        self.search_query = ""
        self.search_results = []
        self.error_message = ""

    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_tui() -> None:
    """Run the SWB TUI application."""
    # Set up logging
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = SWBTUIDirect()
    app.run()


if __name__ == "__main__":
    run_tui()

