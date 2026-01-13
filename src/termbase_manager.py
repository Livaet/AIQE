"""
Term Base Manager

Manages retrieval, caching, and matching of terminology from MemoQ term bases.
"""

from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from loguru import logger
import re
from difflib import SequenceMatcher

from src.models import TermEntry
from src.memoq_client import MemoQClient


class TermBaseManager:
    """
    Manages term base operations including caching and fuzzy matching.
    """

    def __init__(
        self,
        memoq_client: MemoQClient,
        cache_enabled: bool = True,
        cache_ttl: int = 3600,
        case_sensitive: bool = False,
        fuzzy_matching: bool = True,
        fuzzy_threshold: float = 0.9,
    ):
        """
        Initialize Term Base Manager.

        Args:
            memoq_client: MemoQ API client instance
            cache_enabled: Whether to cache term entries
            cache_ttl: Cache time-to-live in seconds
            case_sensitive: Whether term matching is case sensitive
            fuzzy_matching: Enable fuzzy matching for terms
            fuzzy_threshold: Minimum similarity score (0-1) for fuzzy matches
        """
        self.client = memoq_client
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.case_sensitive = case_sensitive
        self.fuzzy_matching = fuzzy_matching
        self.fuzzy_threshold = fuzzy_threshold

        # Cache: {(termbase_guid, source_lang, target_lang): (entries, timestamp)}
        self._cache: Dict[tuple, tuple[List[TermEntry], datetime]] = {}

        logger.info("Initialized Term Base Manager")

    def get_project_terms(
        self,
        project_guid: str,
        source_lang: str,
        target_lang: str,
    ) -> List[TermEntry]:
        """
        Get all term entries from all term bases attached to a project.

        Args:
            project_guid: Project GUID
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            List of all term entries from project term bases
        """
        try:
            # Get termbase GUIDs for the project
            termbase_guids = self.client.get_termbases(project_guid)

            if not termbase_guids:
                logger.warning(f"No termbases found for project {project_guid}")
                return []

            # Collect all terms from all termbases
            all_terms = []
            for tb_guid in termbase_guids:
                terms = self._get_termbase_entries(tb_guid, source_lang, target_lang)
                all_terms.extend(terms)

            # Remove duplicates (keep first occurrence)
            unique_terms = self._deduplicate_terms(all_terms)

            logger.info(
                f"Retrieved {len(unique_terms)} unique terms from {len(termbase_guids)} termbases"
            )

            return unique_terms

        except Exception as e:
            logger.error(f"Failed to get project terms: {e}")
            return []

    def _get_termbase_entries(
        self,
        termbase_guid: str,
        source_lang: str,
        target_lang: str,
    ) -> List[TermEntry]:
        """
        Get entries from a termbase with caching.

        Args:
            termbase_guid: Termbase GUID
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            List of term entries
        """
        cache_key = (termbase_guid, source_lang, target_lang)

        # Check cache
        if self.cache_enabled and cache_key in self._cache:
            entries, timestamp = self._cache[cache_key]

            # Check if cache is still valid
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                logger.debug(f"Using cached terms for termbase {termbase_guid}")
                return entries
            else:
                # Cache expired, remove it
                del self._cache[cache_key]

        # Fetch from API
        entries = self.client.get_termbase_entries(
            termbase_guid, source_lang, target_lang
        )

        # Update cache
        if self.cache_enabled:
            self._cache[cache_key] = (entries, datetime.utcnow())

        return entries

    def _deduplicate_terms(self, terms: List[TermEntry]) -> List[TermEntry]:
        """
        Remove duplicate term entries.

        Args:
            terms: List of term entries

        Returns:
            Deduplicated list
        """
        seen: Set[tuple] = set()
        unique_terms = []

        for term in terms:
            # Create a key for deduplication
            if self.case_sensitive:
                key = (term.source_term, term.target_term, term.source_lang, term.target_lang)
            else:
                key = (
                    term.source_term.lower(),
                    term.target_term.lower(),
                    term.source_lang,
                    term.target_lang,
                )

            if key not in seen:
                seen.add(key)
                unique_terms.append(term)

        return unique_terms

    def find_terms_in_text(
        self,
        text: str,
        terms: List[TermEntry],
        language: str,
        is_source: bool = True,
    ) -> List[TermEntry]:
        """
        Find term entries that appear in the given text.

        Args:
            text: Text to search in
            terms: List of term entries to search for
            language: Language code of the text
            is_source: Whether this is source text (True) or target text (False)

        Returns:
            List of matching term entries
        """
        if not text:
            return []

        matches = []
        search_text = text if self.case_sensitive else text.lower()

        for term in terms:
            # Get the term to search for based on language side
            if is_source:
                search_term = term.source_term
            else:
                search_term = term.target_term

            if not search_term:
                continue

            compare_term = search_term if self.case_sensitive else search_term.lower()

            # Exact match
            if compare_term in search_text:
                matches.append(term)
            # Fuzzy match if enabled
            elif self.fuzzy_matching:
                similarity = self._calculate_similarity(compare_term, search_text)
                if similarity >= self.fuzzy_threshold:
                    matches.append(term)

        return matches

    def check_term_consistency(
        self,
        source_text: str,
        target_text: str,
        terms: List[TermEntry],
    ) -> tuple[List[TermEntry], List[str]]:
        """
        Check if terms found in source are correctly translated in target.

        Args:
            source_text: Source text
            target_text: Target text
            terms: Available term entries

        Returns:
            Tuple of (correctly_used_terms, inconsistency_issues)
        """
        source_terms = self.find_terms_in_text(source_text, terms, "", is_source=True)

        if not source_terms:
            return [], []

        correctly_used = []
        issues = []

        for term in source_terms:
            expected_target = term.target_term

            if not expected_target:
                continue

            compare_target = expected_target if self.case_sensitive else expected_target.lower()
            compare_text = target_text if self.case_sensitive else target_text.lower()

            # Check if forbidden term is used
            if term.forbidden:
                if compare_target in compare_text:
                    issues.append(
                        f"Forbidden term '{term.target_term}' used "
                        f"(source: '{term.source_term}')"
                    )
                continue

            # Check if term is properly translated
            if compare_target in compare_text:
                correctly_used.append(term)
            elif self.fuzzy_matching:
                similarity = self._calculate_similarity(compare_target, compare_text)
                if similarity >= self.fuzzy_threshold:
                    correctly_used.append(term)
                else:
                    issues.append(
                        f"Term '{term.source_term}' may not be correctly translated. "
                        f"Expected: '{term.target_term}'"
                    )
            else:
                issues.append(
                    f"Term '{term.source_term}' may not be correctly translated. "
                    f"Expected: '{term.target_term}'"
                )

        return correctly_used, issues

    def _calculate_similarity(self, term: str, text: str) -> float:
        """
        Calculate similarity between a term and text.

        Uses SequenceMatcher for fuzzy matching.

        Args:
            term: Term to search for
            text: Text to search in

        Returns:
            Similarity score (0-1)
        """
        # Check if term appears as a substring (high priority)
        if term in text:
            return 1.0

        # Split text into words and check similarity with each
        words = re.findall(r'\b\w+\b', text)

        max_similarity = 0.0
        for word in words:
            similarity = SequenceMatcher(None, term, word).ratio()
            max_similarity = max(max_similarity, similarity)

        return max_similarity

    def get_term_context(
        self,
        term_entry: TermEntry,
        include_definition: bool = True,
        include_context: bool = True,
        include_domain: bool = True,
    ) -> str:
        """
        Format term entry information for AI context.

        Args:
            term_entry: Term entry
            include_definition: Include definition
            include_context: Include usage context
            include_domain: Include domain/subject field

        Returns:
            Formatted string with term information
        """
        parts = [
            f"Source: '{term_entry.source_term}' → Target: '{term_entry.target_term}'"
        ]

        if term_entry.forbidden:
            parts.append("(FORBIDDEN TERM - DO NOT USE)")

        if include_definition and term_entry.definition:
            parts.append(f"Definition: {term_entry.definition}")

        if include_context and term_entry.context:
            parts.append(f"Context: {term_entry.context}")

        if include_domain and term_entry.domain:
            parts.append(f"Domain: {term_entry.domain}")

        return " | ".join(parts)

    def clear_cache(self):
        """Clear the term cache."""
        self._cache.clear()
        logger.info("Term cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_entries = sum(len(entries) for entries, _ in self._cache.values())

        return {
            "cached_termbases": len(self._cache),
            "total_cached_entries": total_entries,
        }
