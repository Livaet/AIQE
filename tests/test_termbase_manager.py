"""
Tests for TermBaseManager
"""

import pytest
from unittest.mock import MagicMock

from src.termbase_manager import TermBaseManager
from src.models import TermEntry


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def manager(mock_client):
    return TermBaseManager(
        memoq_client=mock_client,
        cache_enabled=True,
        cache_ttl=3600,
        case_sensitive=False,
        fuzzy_matching=True,
        fuzzy_threshold=0.9,
    )


@pytest.fixture
def sample_terms():
    return [
        TermEntry(source_term="software", target_term="logiciel", source_lang="en", target_lang="fr"),
        TermEntry(source_term="hardware", target_term="matériel", source_lang="en", target_lang="fr"),
        TermEntry(source_term="computer", target_term="ordinateur", source_lang="en", target_lang="fr"),
        TermEntry(source_term="car", target_term="voiture", source_lang="en", target_lang="fr"),
        TermEntry(source_term="car", target_term="automobile", source_lang="en", target_lang="fr", forbidden=True),
    ]


def test_find_terms_in_text_exact_match(manager, sample_terms):
    """Test that exact matches are returned."""
    results = manager.find_terms_in_text("The software is good.", sample_terms, "en", is_source=True)
    source_terms = [t.source_term for t in results]
    assert "software" in source_terms


def test_find_terms_in_text_no_match(manager, sample_terms):
    """Test that non-matching terms are not returned."""
    results = manager.find_terms_in_text("The cat sat on the mat.", sample_terms, "en", is_source=True)
    source_terms = [t.source_term for t in results]
    assert "software" not in source_terms
    assert "hardware" not in source_terms


def test_find_terms_in_text_case_insensitive(manager, sample_terms):
    """Test case-insensitive matching."""
    results = manager.find_terms_in_text("I use SOFTWARE daily.", sample_terms, "en", is_source=True)
    source_terms = [t.source_term for t in results]
    assert "software" in source_terms


def test_find_terms_in_text_multiple(manager, sample_terms):
    """Test that multiple matches are returned."""
    results = manager.find_terms_in_text(
        "The software runs on the computer hardware.", sample_terms, "en", is_source=True
    )
    source_terms = [t.source_term for t in results]
    assert "software" in source_terms
    assert "hardware" in source_terms
    assert "computer" in source_terms


def test_deduplicate_terms(manager, sample_terms):
    """Test term deduplication removes duplicate source terms."""
    # sample_terms has "car" twice (once forbidden)
    duplicated = sample_terms + sample_terms  # Double all terms
    unique = manager._deduplicate_terms(duplicated)

    source_terms = [t.source_term for t in unique]
    # Each source term should appear only once
    assert source_terms.count("software") == 1
    assert source_terms.count("hardware") == 1


def test_get_project_terms_no_termbases(manager, mock_client):
    """Test with project that has no termbases."""
    mock_client.get_termbases.return_value = []

    terms = manager.get_project_terms("project-guid", "en", "fr")
    assert terms == []


def test_get_project_terms_with_termbases(manager, mock_client, sample_terms):
    """Test retrieving terms from project termbases."""
    mock_client.get_termbases.return_value = ["tb-001", "tb-002"]
    mock_client.get_termbase_entries.return_value = sample_terms[:2]

    terms = manager.get_project_terms("project-guid", "en", "fr")

    # Should combine terms from both termbases (2 termbases * 2 terms each = 4, deduplicated)
    assert len(terms) > 0
    assert mock_client.get_termbase_entries.call_count == 2


def test_cache_is_used(manager, mock_client, sample_terms):
    """Test that cache prevents repeated API calls."""
    mock_client.get_termbases.return_value = ["tb-001"]
    mock_client.get_termbase_entries.return_value = sample_terms

    # First call - should hit API
    terms1 = manager.get_project_terms("project-guid", "en", "fr")

    # Second call - should use cache
    terms2 = manager.get_project_terms("project-guid", "en", "fr")

    # The underlying termbase entry method should only be called once
    assert mock_client.get_termbase_entries.call_count == 1
    assert len(terms1) == len(terms2)


def test_cache_disabled(mock_client, sample_terms):
    """Test that disabling cache causes repeated API calls."""
    no_cache_manager = TermBaseManager(
        memoq_client=mock_client,
        cache_enabled=False,
    )

    mock_client.get_termbases.return_value = ["tb-001"]
    mock_client.get_termbase_entries.return_value = sample_terms[:2]

    no_cache_manager.get_project_terms("project-guid", "en", "fr")
    no_cache_manager.get_project_terms("project-guid", "en", "fr")

    assert mock_client.get_termbase_entries.call_count == 2
