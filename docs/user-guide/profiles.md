# Library Catalog Profiles

The SWB client supports multiple German library union catalogs through pre-configured profiles, making it easy to search different catalogs without manually specifying endpoint URLs.

## Available Profiles

### SWB (Default)
```bash
swb search "query" --profile swb
```

- **Name**: Südwestdeutscher Bibliotheksverbund
- **Region**: Baden-Württemberg, Saarland, Saxony
- **URL**: `https://sru.k10plus.de/swb`
- **Best for**: Books in southwestern German libraries

### K10plus
```bash
swb search "query" --profile k10plus
```

- **Name**: K10plus Verbundkatalog
- **Region**: Northern and southwestern Germany
- **URL**: `https://sru.k10plus.de/opac-de-627`
- **Best for**: Widest coverage including many NRW libraries

### DNB
```bash
swb search "query" --profile dnb
```

- **Name**: Deutsche Nationalbibliothek
- **Region**: National (all of Germany)
- **URL**: `https://services.dnb.de/sru/dnb`
- **Best for**: Comprehensive national bibliography

### GBV
```bash
swb search "query" --profile gvk
```

- **Name**: Gemeinsamer Verbundkatalog (GBV)
- **Region**: Northern Germany
- **URL**: `https://sru.gbv.de/gvk`
- **Best for**: Northern German libraries

### BVB
```bash
swb search "query" --profile bvb
```

- **Name**: Bibliotheksverbund Bayern
- **Region**: Bavaria
- **URL**: `https://sru.bib-bvb.de/bvb`
- **Best for**: Bavarian libraries

### HeBIS
```bash
swb search "query" --profile hebis
```

- **Name**: Hessisches BibliotheksInformationsSystem
- **Region**: Hesse and parts of Rhineland-Palatinate
- **URL**: `https://sru.hebis.de/sru`
- **Best for**: Libraries in Hesse

## Listing Profiles

View all available profiles with their details:

```bash
swb profiles
```

Output:
```
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name    ┃ Display Name                      ┃ Region                      ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ swb     │ SWB (Südwestdeutscher             │ Baden-Württemberg,          │
│         │ Bibliotheksverbund)               │ Saarland, Sachsen           │
│ k10plus │ K10plus Verbundkatalog            │ Norddeutschland,            │
│         │                                   │ Südwestdeutschland          │
│ ...     │ ...                               │ ...                         │
└─────────┴───────────────────────────────────┴─────────────────────────────┘
```

## Using Profiles

### With Search

```bash
# Search K10plus
swb search "Python programming" --profile k10plus

# Search DNB
swb search "Goethe" --profile dnb --max 20
```

### With ISBN/ISSN

```bash
# Check holdings in K10plus
swb isbn 978-3-16-148410-0 --profile k10plus --holdings

# Search ISSN in DNB
swb issn 0028-0836 --profile dnb
```

### With Related Records

```bash
# Find related records in different catalog
swb related 267838395 --relation-type child --profile k10plus
```

### With Scan

```bash
# Scan authors in DNB
swb scan "pica.per=Goethe" --profile dnb
```

### With Explain

```bash
# Get server capabilities for different profiles
swb explain --profile k10plus
swb explain --profile dnb
```

## Profile Priority

When multiple options are specified, they are applied in this order:

1. **Custom URL** (highest priority)
2. **Profile option**
3. **Default profile** (swb)

Example:

```bash
# Custom URL overrides profile
swb search "query" --profile k10plus --url https://custom.endpoint.de/sru
# Uses: custom.endpoint.de

# Profile overrides default
swb search "query" --profile dnb
# Uses: services.dnb.de

# Default when nothing specified
swb search "query"
# Uses: sru.k10plus.de/swb
```

## Regional Coverage

### Which Profile to Use?

**For general searches:** Use `k10plus` - it has the widest coverage

**By region:**

- **Baden-Württemberg, Saarland**: `swb`
- **Bavaria**: `bvb`
- **Hesse**: `hebis`
- **Northern Germany**: `gvk` or `k10plus`
- **National coverage**: `dnb`
- **NRW libraries**: `k10plus` (includes many NRW holdings)

**By library type:**

- **University libraries**: `k10plus` or regional profile
- **National bibliography**: `dnb`
- **Public libraries**: Regional profile (`swb`, `bvb`, `hebis`)

## Custom Endpoints

If you need to access a catalog not in the profiles:

```bash
swb search "query" --url https://your-sru-endpoint.de/sru
```

This bypasses profile selection and connects directly to your custom URL.

## Comparing Catalogs

Search the same query across multiple catalogs:

```bash
# Search in SWB
swb isbn 978-3-17-042177-6 --profile swb --holdings

# Same search in K10plus
swb isbn 978-3-17-042177-6 --profile k10plus --holdings

# Same search in DNB
swb isbn 978-3-17-042177-6 --profile dnb
```

This helps find the most complete holdings information.

## Technical Details

### Profile Configuration

Profiles are defined in `src/swb/profiles.py`:

```python
@dataclass
class CatalogProfile:
    name: str
    url: str
    display_name: str
    description: str
    region: str
```

### Adding Custom Profiles

To add a custom profile programmatically:

```python
from swb.profiles import PROFILES, CatalogProfile

# Add custom profile
PROFILES["custom"] = CatalogProfile(
    name="custom",
    url="https://custom.sru.endpoint.de/sru",
    display_name="Custom Library Network",
    description="My custom library network",
    region="Custom Region"
)

# Use it
from swb import SWBClient
client = SWBClient(base_url=PROFILES["custom"].url)
```

## Profile Limitations

!!! warning "Important Notes"
    - Not all profiles support all features
    - Some catalogs may have access restrictions
    - Holdings information varies by catalog
    - Response times differ between servers
    - Some profiles may require VPN access

### Common Issues

**403 Forbidden Error:**
- Try a different profile (`k10plus` or `dnb`)
- Check if catalog requires authentication
- Some catalogs may block certain IPs

**No Results:**
- Not all content is in all catalogs
- Try broader search terms
- Use DNB for comprehensive national coverage

**Slow Responses:**
- Some servers are slower than others
- Consider using `k10plus` for best performance
- Adjust timeout in code if needed

## Next Steps

- [CLI Reference](cli.md) - All command line options
- [Advanced Features](advanced.md) - CQL queries and more
- [API Reference](../api/profiles.md) - Use profiles in code
