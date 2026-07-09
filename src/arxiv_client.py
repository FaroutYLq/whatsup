"""
ArXiv client for fetching and filtering papers
"""

import re
import arxiv
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple


# Strip a trailing version suffix (e.g. "2401.12345v3" -> "2401.12345")
# so replacements/cross-lists dedup against the original submission.
_VERSION_SUFFIX = re.compile(r"v\d+$")

# Safety cap on how many results we page through per category before we
# assume something is wrong with the cutoff logic. In practice we break
# out much earlier when results fall past the date cutoff. Set well above
# any plausible multi-day submission volume for a single category.
_MAX_RESULTS_PER_CATEGORY = 2000


class ArxivClient:
    """Fetch papers from ArXiv with category and keyword filtering."""

    def __init__(
        self,
        categories: List[str],
        keywords: List[str] = None,
        max_days_back: int = 1,
        keyword_filter: bool = False
    ):
        """
        Initialize the ArXiv client.

        Args:
            categories: List of arxiv categories to search
            keywords: List of keywords for pre-filtering
            max_days_back: How many days back to search
            keyword_filter: If True, only papers matching a keyword are
                kept (a cost-saver). If False (default), keywords are
                ignored and every fetched paper is passed to the LLM so
                nothing is dropped by a substring miss.
        """
        self.categories = categories
        self.keywords = keywords or []
        self.max_days_back = max_days_back
        self.keyword_filter = keyword_filter

        # Modern arxiv client with built-in retry/backoff. This retries
        # transient failures (including UnexpectedEmptyPageError) instead
        # of silently truncating a category the way the deprecated
        # Search.results() iterator did.
        self._client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=5
        )

    def fetch_papers(
        self,
        max_results: int = _MAX_RESULTS_PER_CATEGORY
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Fetch papers from ArXiv.

        Args:
            max_results: Safety cap on results paged per category.

        Returns:
            (unique_papers, failed_categories) where failed_categories
            lists categories that could not be fetched after retries.
        """
        all_papers = []
        failed_categories = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(
            days=self.max_days_back
        )

        for category in self.categories:
            # Build search query for this category
            query = f"cat:{category}"

            # Sort by last-updated so cross-lists and delayed/late
            # announcements (whose original submission date is old but
            # which only appeared in the listing now) are not missed.
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.LastUpdatedDate,
                sort_order=arxiv.SortOrder.Descending
            )

            try:
                category_papers = self._fetch_category(
                    search, cutoff_date
                )
                all_papers.extend(category_papers)
            except Exception as e:
                # Loud failure: record the category so the digest can
                # tell the user coverage was incomplete, rather than
                # silently emailing a partial digest that looks normal.
                print(
                    f"  Warning: Error fetching {category} "
                    f"after retries: {e}"
                )
                failed_categories.append(category)
                continue

        # Remove duplicates (papers in multiple categories, or a
        # replacement matching its original submission).
        unique_papers = self._deduplicate_papers(all_papers)

        return unique_papers, failed_categories

    def _fetch_category(
        self,
        search: "arxiv.Search",
        cutoff_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Page through one category until results fall past the cutoff.

        Because results are sorted by LastUpdatedDate descending, the
        first result older than the cutoff means every subsequent result
        is older too, so we stop — this guarantees full coverage of the
        window regardless of how many papers were submitted, instead of
        capping at a fixed page of 100.
        """
        papers = []

        for result in self._client.results(search):
            # 'updated' reflects when the paper last appeared in the
            # listing (new submission, replacement, or cross-list).
            if result.updated < cutoff_date:
                break

            paper = {
                'title': result.title,
                'abstract': result.summary,
                'authors': ', '.join(
                    [a.name for a in result.authors]
                ),
                'published': result.published.strftime('%Y-%m-%d'),
                'updated': result.updated.strftime('%Y-%m-%d'),
                'url': result.entry_id,
                'arxiv_id': self._versionless_id(result),
                'categories': result.categories,
                'pdf_url': result.pdf_url,
                # 'new' = first announced in this window; 'updated' =
                # replacement/cross-list of an older submission.
                'status': (
                    'new'
                    if result.published >= cutoff_date
                    else 'updated'
                ),
            }

            if self.keyword_filter and self.keywords:
                if self._matches_keywords(paper):
                    papers.append(paper)
            else:
                papers.append(paper)

        return papers

    def _versionless_id(self, result: "arxiv.Result") -> str:
        """Return the arXiv id with any version suffix stripped."""
        short_id = result.get_short_id()
        return _VERSION_SUFFIX.sub("", short_id)

    def _matches_keywords(self, paper: Dict[str, Any]) -> bool:
        """
        Check if paper matches any keyword (word-boundary match).

        Args:
            paper: Paper dictionary

        Returns:
            True if paper matches any keyword
        """
        text = f"{paper['title']} {paper['abstract']}".lower()

        for keyword in self.keywords:
            kw = keyword.lower().strip()
            if not kw:
                continue
            # Word-boundary match so "THz" doesn't spuriously match
            # inside another token, while still matching the whole word.
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return True

        return False

    def _deduplicate_papers(
        self,
        papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate papers based on versionless arXiv id.

        Args:
            papers: List of papers

        Returns:
            Deduplicated list
        """
        seen_ids = set()
        unique_papers = []

        for paper in papers:
            key = paper.get('arxiv_id') or paper['url']
            if key not in seen_ids:
                seen_ids.add(key)
                unique_papers.append(paper)

        return unique_papers
