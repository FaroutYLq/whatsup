"""
Parser for Zotero library exports (BibTeX or JSON)
"""

import json
import bibtexparser
from pathlib import Path
from typing import List, Dict, Any


class ZoteroParser:
    """Parse Zotero library to extract research interests."""
    
    def __init__(self, library_file: str):
        """
        Initialize the Zotero parser.
        
        Args:
            library_file: Path to BibTeX or JSON export file
        """
        self.library_file = Path(library_file)
        self.papers = []
        
        if self.library_file.exists():
            self._parse_library()
    
    def _parse_library(self) -> None:
        """Parse the library file based on extension."""
        suffix = self.library_file.suffix.lower()
        
        if suffix == '.bib':
            self._parse_bibtex()
        elif suffix == '.json':
            self._parse_json()
        else:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                "Use .bib or .json"
            )
    
    def _parse_bibtex(self) -> None:
        """Parse BibTeX export."""
        with open(self.library_file, 'r', encoding='utf-8') as f:
            bib_database = bibtexparser.load(f)
        
        for entry in bib_database.entries:
            paper = {
                'title': entry.get('title', ''),
                'abstract': entry.get('abstract', ''),
                'author': entry.get('author', ''),
                'year': entry.get('year', ''),
                'keywords': entry.get('keywords', '')
            }
            self.papers.append(paper)
    
    def _parse_json(self) -> None:
        """Parse JSON export."""
        with open(self.library_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures from Zotero
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and 'items' in data:
            items = data['items']
        else:
            items = []
        
        for item in items:
            # Extract relevant fields
            title = item.get('title', '')
            abstract_note = item.get('abstractNote', '')
            creators = item.get('creators', [])
            
            # Format authors
            authors = ', '.join(
                f"{c.get('firstName', '')} "
                f"{c.get('lastName', '')}"
                for c in creators if 'lastName' in c
            )
            
            paper = {
                'title': title,
                'abstract': abstract_note,
                'author': authors,
                'year': item.get('date', '')[:4] 
                if 'date' in item else '',
                'keywords': ', '.join(
                    item.get('tags', [])
                ) if isinstance(
                    item.get('tags'), list
                ) else ''
            }
            self.papers.append(paper)
    
    def get_papers(self) -> List[Dict[str, str]]:
        """Get the list of parsed papers."""
        return self.papers
    
    def get_summary(
        self, 
        include_all_titles: bool = True,
        detailed_papers: int = 30
    ) -> str:
        """
        Get a text summary of the library for LLM.
        
        Args:
            include_all_titles: Include all paper titles
            detailed_papers: Number of papers with abstracts
            
        Returns:
            Formatted summary string
        """
        if not self.papers:
            return "No Zotero library provided."
        
        summary_lines = [
            f"Research Background from Zotero library "
            f"({len(self.papers)} papers):",
            ""
        ]
        
        # Section 1: Recent papers with abstracts
        if detailed_papers > 0:
            summary_lines.extend([
                f"Recent papers with details "
                f"(most recent {detailed_papers}):",
                ""
            ])
            
            papers_with_abstracts = self.papers[:detailed_papers]
            
            for i, paper in enumerate(papers_with_abstracts, 1):
                title = paper.get('title', 'No title')
                abstract = paper.get('abstract', '')
                
                # Truncate very long abstracts
                if len(abstract) > 200:
                    abstract = abstract[:200] + "..."
                
                summary_lines.append(f"{i}. {title}")
                if abstract:
                    summary_lines.append(
                        f"   Abstract: {abstract}"
                    )
                summary_lines.append("")
        
        # Section 2: All remaining titles (compact)
        if include_all_titles and len(self.papers) > detailed_papers:
            summary_lines.extend([
                "",
                f"Additional papers in library "
                f"({len(self.papers) - detailed_papers} more):",
                ""
            ])
            
            remaining_papers = self.papers[detailed_papers:]
            for paper in remaining_papers:
                title = paper.get('title', 'No title')
                # Just titles, very compact
                summary_lines.append(f"- {title}")
        
        return "\n".join(summary_lines)

