"""Library catalog profiles for different SRU endpoints.

This module defines pre-configured profiles for accessing different German
library union catalogs via their SRU interfaces.
"""

from dataclasses import dataclass


@dataclass
class CatalogProfile:
    """Represents a library catalog profile.

    Attributes:
        name: Short identifier for the profile
        url: Base URL for the SRU endpoint
        display_name: Human-readable name
        description: Description of what this catalog covers
        region: Geographic or institutional coverage
    """

    name: str
    url: str
    display_name: str
    description: str
    region: str


# Predefined catalog profiles
PROFILES = {
    "swb": CatalogProfile(
        name="swb",
        url="https://sru.k10plus.de/swb",
        display_name="SWB (Südwestdeutscher Bibliotheksverbund)",
        description="Library network covering Baden-Württemberg, Saarland, and Saxony",
        region="Baden-Württemberg, Saarland, Sachsen",
    ),
    "k10plus": CatalogProfile(
        name="k10plus",
        url="https://sru.k10plus.de/opac-de-627",
        display_name="K10plus Verbundkatalog",
        description="Union catalog covering northern and southwestern Germany",
        region="Norddeutschland, Südwestdeutschland",
    ),
    "gvk": CatalogProfile(
        name="gvk",
        url="https://sru.gbv.de/gvk",
        display_name="GBV (Gemeinsamer Verbundkatalog)",
        description="Common union catalog of the GBV library network",
        region="Norddeutschland",
    ),
    "dnb": CatalogProfile(
        name="dnb",
        url="https://services.dnb.de/sru/dnb",
        display_name="DNB (Deutsche Nationalbibliothek)",
        description="German National Library catalog",
        region="Deutschland (National)",
    ),
    "bvb": CatalogProfile(
        name="bvb",
        url="https://sru.bib-bvb.de/bvb",
        display_name="BVB (Bibliotheksverbund Bayern)",
        description="Bavarian Library Network",
        region="Bayern",
    ),
    "hebis": CatalogProfile(
        name="hebis",
        url="https://sru.hebis.de/sru",
        display_name="HeBIS (Hessisches BibliotheksInformationsSystem)",
        description="Library network for Hesse and parts of Rhineland-Palatinate",
        region="Hessen, Rheinland-Pfalz (teilweise)",
    ),
}

# Default profile
DEFAULT_PROFILE = "swb"


def get_profile(name: str) -> CatalogProfile:
    """Get a catalog profile by name.

    Args:
        name: Profile identifier (e.g., 'swb', 'k10plus', 'dnb')

    Returns:
        CatalogProfile object

    Raises:
        ValueError: If profile name is unknown
    """
    name_lower = name.lower()
    if name_lower not in PROFILES:
        available = ", ".join(PROFILES.keys())
        raise ValueError(
            f"Unknown profile: {name}. Available profiles: {available}"
        )
    return PROFILES[name_lower]


def list_profiles() -> list[CatalogProfile]:
    """Get a list of all available catalog profiles.

    Returns:
        List of CatalogProfile objects sorted by name
    """
    return sorted(PROFILES.values(), key=lambda p: p.name)
