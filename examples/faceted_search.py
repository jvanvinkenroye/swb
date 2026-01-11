"""Example demonstrating faceted search with SRU 2.0.

This example shows how to use the faceted search feature to explore
result distribution across different categories.

Note: Faceted search requires SRU 2.0 support from the server.
"""

from swb.api import SWBClient
from swb.models import SearchIndex

# Create client
client = SWBClient()

print("=" * 80)
print("Faceted Search Example (SRU 2.0)")
print("=" * 80)
print()

# Example 1: Search with facets by year and author
print("Example 1: Search 'Python' with year and author facets")
print("-" * 80)

try:
    response = client.search(
        query="Python",
        index=SearchIndex.TITLE,
        maximum_records=5,
        facets=["year", "author"],
        facet_limit=10,
    )

    print(f"Total results: {response.total_results}")
    print(f"Records returned: {len(response.results)}")
    print()

    # Display first few results
    print("Sample results:")
    for idx, result in enumerate(response.results[:3], 1):
        print(f"  {idx}. {result.title or 'N/A'} ({result.year or 'N/A'})")
        if result.author:
            print(f"     Author: {result.author}")
    print()

    # Display facets
    if response.facets:
        print("Facets:")
        for facet in response.facets:
            print(f"\n  {facet.name}:")
            for value in facet.values[:5]:  # Show top 5
                print(f"    {value.value}: {value.count}")
    else:
        print("Note: Server does not support facets or returned no facet data.")

except Exception as e:
    print(f"Error: {e}")
    print("\nNote: This example requires network connectivity to the SRU server.")
    print("Faceted search also requires SRU 2.0 support from the server.")

print()
print("=" * 80)
print("Example 2: Search with subject facets")
print("-" * 80)

try:
    response = client.search(
        query="Machine Learning",
        maximum_records=3,
        facets=["year", "subject"],
        facet_limit=15,
    )

    print(f"Total results: {response.total_results}")
    print()

    if response.facets:
        print("Facets:")
        for facet in response.facets:
            print(f"\n  {facet.name}:")
            for value in facet.values[:7]:  # Show top 7
                print(f"    {value.value}: {value.count}")
    else:
        print("Note: No facet data available.")

except Exception as e:
    print(f"Error: {e}")

print()
print("=" * 80)
print("Done!")
print()
print("CLI Usage:")
print("  swb search 'Python' --facets year,author --facet-limit 20")
print("  swb search 'Machine Learning' --facets year,subject --max 10")
print("=" * 80)
