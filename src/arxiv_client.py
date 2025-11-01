"""
ArXiv client for fetching and filtering papers
"""

import arxiv
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any


class ArxivClient:
    """Fetch papers from ArXiv with category and keyword filtering."""
    
    def __init__(
        self, 
        categories: List[str],
        keywords: List[str] = None,
        max_days_back: int = 1
    ):
        """
        Initialize the ArXiv client.
        
        Args:
            categories: List of arxiv categories to search
            keywords: List of keywords for pre-filtering
            max_days_back: How many days back to search
        """
        self.categories = categories
        self.keywords = keywords or []
        self.max_days_back = max_days_back
    
    def fetch_papers(
        self, 
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch papers from ArXiv.
        
        Args:
            max_results: Maximum papers to fetch per category
            
        Returns:
            List of paper dictionaries
        """
        all_papers = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(
            days=self.max_days_back
        )
        
        for category in self.categories:
            # Build search query for this category
            query = f"cat:{category}"
            
            # Search ArXiv
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            try:
                for result in search.results():
                    # Check if paper is recent enough
                    if result.published < cutoff_date:
                        continue
                    
                    paper = {
                        'title': result.title,
                        'abstract': result.summary,
                        'authors': ', '.join(
                            [a.name for a in result.authors]
                        ),
                        'published': result.published.strftime(
                            '%Y-%m-%d'
                        ),
                        'url': result.entry_id,
                        'categories': result.categories,
                        'pdf_url': result.pdf_url
                    }
                    
                    # Apply keyword pre-filtering if keywords exist
                    if self.keywords:
                        if self._matches_keywords(paper):
                            all_papers.append(paper)
                    else:
                        all_papers.append(paper)
            except arxiv.UnexpectedEmptyPageError:
                # ArXiv API returned empty page, no more results
                print(
                    f"  Note: ArXiv API returned empty page "
                    f"for {category}, continuing..."
                )
                continue
            except Exception as e:
                print(
                    f"  Warning: Error fetching {category}: {e}"
                )
                continue
        
        # Remove duplicates (papers in multiple categories)
        unique_papers = self._deduplicate_papers(all_papers)
        
        return unique_papers
    
    def _matches_keywords(self, paper: Dict[str, Any]) -> bool:
        """
        Check if paper matches any of the keywords.
        
        Args:
            paper: Paper dictionary
            
        Returns:
            True if paper matches any keyword
        """
        text = (
            f"{paper['title']} {paper['abstract']}"
        ).lower()
        
        for keyword in self.keywords:
            if keyword.lower() in text:
                return True
        
        return False
    
    def _deduplicate_papers(
        self, 
        papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate papers based on URL.
        
        Args:
            papers: List of papers
            
        Returns:
            Deduplicated list
        """
        seen_urls = set()
        unique_papers = []
        
        for paper in papers:
            if paper['url'] not in seen_urls:
                seen_urls.add(paper['url'])
                unique_papers.append(paper)
        
        return unique_papers

