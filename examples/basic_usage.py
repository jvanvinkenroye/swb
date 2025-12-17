#!/usr/bin/env python3
"""Example script demonstrating basic usage of the SWB API client."""

from swb import RecordFormat, SearchIndex, SWBClient


def main() -> None:
    """Demonstrate basic SWB API usage."""
    # Create a client instance
    with SWBClient() as client:
        print("=" * 80)
        print("SWB API Client - Basic Usage Examples")
        print("=" * 80)
        print()

        # Example 1: Simple keyword search
        print("Example 1: Search for books about Python")
        print("-" * 80)
        response = client.search(
            query="Python",
            index=SearchIndex.TITLE,
            maximum_records=5,
        )

        print(f"Found {response.total_results} total results")
        print(f"Showing first {len(response.results)} results:\n")

        for idx, result in enumerate(response.results, 1):
            print(f"{idx}. {result.title}")
            if result.author:
                print(f"   Author: {result.author}")
            if result.year:
                print(f"   Year: {result.year}")
            if result.isbn:
                print(f"   ISBN: {result.isbn}")
            print()

        # Example 2: Search by ISBN
        print("\nExample 2: Search by ISBN")
        print("-" * 80)
        response = client.search_by_isbn("978-3-16-148410-0")

        if response.results:
            result = response.results[0]
            print(f"Title: {result.title}")
            print(f"Author: {result.author}")
            print(f"Year: {result.year}")
            print(f"Publisher: {result.publisher}")
        else:
            print("No results found for this ISBN")

        # Example 3: Author search with MODS format
        print("\n\nExample 3: Search for works by Goethe (MODS format)")
        print("-" * 80)
        response = client.search(
            query="Goethe",
            index=SearchIndex.AUTHOR,
            record_format=RecordFormat.MODS,
            maximum_records=3,
        )

        print(f"Found {response.total_results} works by Goethe")
        print(f"Showing first {len(response.results)}:\n")

        for idx, result in enumerate(response.results, 1):
            print(f"{idx}. {result.title or 'N/A'}")
            print(f"   Year: {result.year or 'N/A'}")
            print()

        # Example 4: Complex CQL query
        print("\nExample 4: Complex CQL query (Python books from 2023)")
        print("-" * 80)
        response = client.search(
            query='pica.tit="Python" and pica.ejr="2023"',
            maximum_records=3,
        )

        print(f"Found {response.total_results} results")
        for idx, result in enumerate(response.results, 1):
            print(f"{idx}. {result.title}")
            print(f"   Year: {result.year}")
            print()

        # Example 5: Pagination
        print("\nExample 5: Pagination - Get second page of results")
        print("-" * 80)
        first_page = client.search(
            query="Machine Learning",
            index=SearchIndex.SUBJECT,
            maximum_records=5,
            start_record=1,
        )

        if first_page.has_more:
            second_page = client.search(
                query="Machine Learning",
                index=SearchIndex.SUBJECT,
                maximum_records=5,
                start_record=first_page.next_record,
            )
            print(f"Second page ({len(second_page.results)} results):")
            for idx, result in enumerate(second_page.results, 1):
                print(f"{idx}. {result.title}")
        else:
            print("No more results available")


if __name__ == "__main__":
    main()
