# Advanced Features

Advanced usage patterns and techniques for power users.

## CQL Query Language

### Boolean Operators

```bash
# AND
swb search 'pica.tit="Python" and pica.per="Guido"'

# OR
swb search 'pica.tit="Python" or pica.tit="Java"'

# NOT
swb search 'pica.tit="Python" not pica.tit="2.7"'
```

### Wildcards

```bash
# Single character: ?
swb search 'pica.per="Goethe, J?hann"'

# Multiple characters: *
swb search 'pica.tit="Pytho*"'

# Both
swb search 'pica.tit="*learning*"'
```

### Phrase Searches

```bash
# Exact phrase
swb search 'pica.tit="Machine Learning"'

# Without quotes (word search)
swb search 'pica.tit=Machine Learning'
```

### Date Ranges

```bash
# Exact year
swb search 'pica.ejr=2023'

# After year
swb search 'pica.ejr>2020'

# Before year
swb search 'pica.ejr<2010'

# Range
swb search 'pica.ejr>=2020 and pica.ejr<=2023'
```

### Complex Queries

```bash
# Multiple conditions
swb search 'pica.tit="Python" and pica.ejr>2020 and pica.per="*Guido*"'

# Grouping
swb search '(pica.tit="Python" or pica.tit="Java") and pica.ejr>2020'
```

## Index Scanning

### Auto-Completion

Find terms starting with a prefix:

```bash
# Author names
swb scan "pica.per=Goe"
# Returns: Goethe, Johann Wolfgang von (28,531 records)
#          Goebel, Klaus (127 records)
#          ...

# Titles
swb scan "pica.tit=Python"
# Returns: Python (12,345 records)
#          Python Programming (3,456 records)
#          ...
```

### Browse Index

Explore available terms:

```bash
# Browse subjects
swb scan "pica.sub=Informatik" --max 50

# Browse publishers
swb scan "pica.vlg=Springer" --max 20
```

### Response Position

Start at different position in results:

```bash
# Start at 11th term
swb scan "pica.per=Goe" --position 11
```

## Band/Linking Search

### Multi-Volume Works

```bash
# Find all volumes
swb related 267838395 --relation-type child --max 100

# Find parent work
swb related 123456789 --relation-type parent
```

### Series

```bash
# Find all works in series
swb related 267838395 --relation-type family --max 50
```

### Related Works

```bash
# Non-hierarchical relations
swb related 111222333 --relation-type related

# Thesaurus relations
swb related 444555666 --relation-type thesaurus
```

### Record Types

```bash
# Search authority records
swb related 111222333 --relation-type related --record-type authority

# Search bibliographic records (default)
swb related 111222333 --relation-type related --record-type bibliographic
```

## Record Formats

### XML Formats

```bash
# MARCXML (most detailed)
swb search "Python" --format marcxml

# TurboMARC (optimized)
swb search "Python" --format turbomarc

# PICA XML
swb search "Python" --format picaxml
```

### Metadata Formats

```bash
# MODS (structured metadata)
swb search "Python" --format mods

# Dublin Core (simple)
swb search "Python" --format dc

# ISBD (display format)
swb search "Python" --format isbd
```

### Packing Modes

```bash
# XML packing (parsed, default)
swb search "Python" --packing xml

# String packing (raw escaped XML)
swb search "Python" --packing string --raw
```

## Batch Processing

### Process Multiple ISBNs

```bash
# From file
while read isbn; do
    swb isbn "$isbn" --holdings >> results.txt
done < isbns.txt
```

### Search Multiple Terms

```bash
# From array
terms=("Python" "Java" "JavaScript")
for term in "${terms[@]}"; do
    swb search "$term" --max 5
done
```

### Export All Results

```bash
# Paginated export
for i in {1..10}; do
    start=$((($i - 1) * 100 + 1))
    swb search "Python" --start-record $start --max 100 --output "results_$i.txt"
done
```

## Python Integration

### Simple Script

```python
from swb import SWBClient

with SWBClient() as client:
    response = client.search("Python", maximum_records=100)

    for result in response.results:
        if result.year and int(result.year) > 2020:
            print(f"{result.title} ({result.year})")
```

### Advanced Processing

```python
from swb import SWBClient, SearchIndex, SortBy, SortOrder

def find_recent_books(query: str, min_year: int = 2020):
    """Find recent books on a topic."""
    with SWBClient() as client:
        response = client.search(
            query,
            index=SearchIndex.SUBJECT,
            sort_by=SortBy.YEAR,
            sort_order=SortOrder.DESCENDING,
            maximum_records=50
        )

        recent = [
            r for r in response.results
            if r.year and int(r.year) >= min_year
        ]

        return recent

# Use it
books = find_recent_books("Machine Learning", min_year=2022)
for book in books:
    print(f"{book.title} - {book.year}")
```

### Holdings Analysis

```python
from swb import SWBClient
from collections import Counter

def analyze_holdings(isbn: str):
    """Analyze library holdings for a book."""
    with SWBClient() as client:
        response = client.search_by_isbn(isbn)

        if not response.results:
            return None

        book = response.results[0]
        libraries = [h.library_name for h in book.holdings]

        return {
            "title": book.title,
            "total_holdings": len(book.holdings),
            "libraries": Counter(libraries),
            "online_access": sum(1 for h in book.holdings if h.access_url)
        }

# Use it
stats = analyze_holdings("978-3-17-042177-6")
print(f"Available at {stats['total_holdings']} locations")
print(f"Online access: {stats['online_access']}")
```

## Performance Tips

### Reduce Maximum Records

```bash
# Instead of
swb search "Python" --max 100

# Use
swb search "Python" --max 20
```

### Use Specific Indices

```bash
# Faster
swb search "Goethe" --index author

# Slower
swb search "Goethe" --index all
```

### Cache Results

```python
from functools import lru_cache
from swb import SWBClient

@lru_cache(maxsize=100)
def cached_search(query: str):
    with SWBClient() as client:
        return client.search(query)
```

## Troubleshooting

### Debug Mode

```bash
# Show detailed logs
swb --verbose search "Python"

# Or set environment variable
export LOG_LEVEL=DEBUG
swb search "Python"
```

### Connection Issues

```python
from swb import SWBClient

# Increase timeout
client = SWBClient(timeout=60)
```

### Profile Issues

```bash
# Try different profiles
swb search "Python" --profile k10plus
swb search "Python" --profile dnb
```

## Best Practices

1. **Start broad, refine**: Begin with general terms, add filters
2. **Use appropriate indices**: Author for names, Title for works
3. **Leverage profiles**: K10plus for coverage, DNB for completeness
4. **Check holdings**: Add --holdings for availability
5. **Export results**: Save to files for further processing
6. **Handle errors**: Use try-catch in scripts
7. **Respect servers**: Don't hammer endpoints

## Next Steps

- [API Reference](../api/overview.md) - Python integration
- [Development](../development/contributing.md) - Contribute
