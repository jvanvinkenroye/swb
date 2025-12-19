"""Tests for the profiles module."""

import pytest

from swb.profiles import (
    PROFILES,
    CatalogProfile,
    get_profile,
    list_profiles,
)


def test_catalog_profile_dataclass():
    """Test CatalogProfile dataclass creation."""
    profile = CatalogProfile(
        name="test",
        url="https://test.example.com/sru",
        display_name="Test Catalog",
        description="Test description",
        region="Test Region",
    )
    assert profile.name == "test"
    assert profile.url == "https://test.example.com/sru"
    assert profile.display_name == "Test Catalog"
    assert profile.description == "Test description"
    assert profile.region == "Test Region"


def test_profiles_dict_contains_expected_profiles():
    """Test that PROFILES dict contains expected catalog profiles."""
    expected_profiles = {"swb", "k10plus", "gvk", "dnb", "bvb", "hebis"}
    assert set(PROFILES.keys()) == expected_profiles


def test_get_profile_swb():
    """Test getting the SWB profile."""
    profile = get_profile("swb")
    assert profile.name == "swb"
    assert profile.url == "https://sru.k10plus.de/swb"
    assert "SWB" in profile.display_name
    assert "Baden-Württemberg" in profile.region


def test_get_profile_k10plus():
    """Test getting the K10plus profile."""
    profile = get_profile("k10plus")
    assert profile.name == "k10plus"
    assert profile.url == "https://sru.k10plus.de/opac-de-627"
    assert "K10plus" in profile.display_name


def test_get_profile_case_insensitive():
    """Test that get_profile is case-insensitive."""
    profile1 = get_profile("SWB")
    profile2 = get_profile("swb")
    profile3 = get_profile("SwB")
    assert profile1 == profile2 == profile3


def test_get_profile_unknown_raises_error():
    """Test that get_profile raises ValueError for unknown profiles."""
    with pytest.raises(ValueError, match="Unknown profile: unknown"):
        get_profile("unknown")


def test_get_profile_unknown_error_shows_available():
    """Test that error message shows available profiles."""
    with pytest.raises(ValueError, match="Available profiles:"):
        get_profile("nonexistent")


def test_list_profiles_returns_all():
    """Test that list_profiles returns all profiles."""
    profiles = list_profiles()
    assert len(profiles) == 6
    assert all(isinstance(p, CatalogProfile) for p in profiles)


def test_list_profiles_sorted_by_name():
    """Test that list_profiles returns profiles sorted by name."""
    profiles = list_profiles()
    names = [p.name for p in profiles]
    assert names == sorted(names)


def test_all_profiles_have_required_fields():
    """Test that all profiles have required fields populated."""
    for profile in PROFILES.values():
        assert profile.name
        assert profile.url
        assert profile.display_name
        assert profile.description
        assert profile.region
        assert profile.url.startswith("https://")


def test_dnb_profile():
    """Test the DNB (Deutsche Nationalbibliothek) profile."""
    profile = get_profile("dnb")
    assert profile.name == "dnb"
    assert "dnb.de" in profile.url
    assert "Deutsche Nationalbibliothek" in profile.display_name
    assert "National" in profile.region


def test_gvk_profile():
    """Test the GBV/GVK profile."""
    profile = get_profile("gvk")
    assert profile.name == "gvk"
    assert "gbv.de" in profile.url
    assert "GBV" in profile.display_name or "GVK" in profile.display_name


def test_bvb_profile():
    """Test the BVB (Bibliotheksverbund Bayern) profile."""
    profile = get_profile("bvb")
    assert profile.name == "bvb"
    assert "bvb" in profile.url.lower()
    assert "Bayern" in profile.region


def test_hebis_profile():
    """Test the HeBIS profile."""
    profile = get_profile("hebis")
    assert profile.name == "hebis"
    assert "hebis" in profile.url.lower()
    assert "Hessen" in profile.region
