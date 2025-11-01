"""
Main orchestrator for the ArXiv Daily Digest system
"""

import sys
from pathlib import Path

from config_parser import ConfigParser
from zotero_parser import ZoteroParser
from arxiv_client import ArxivClient
from llm_evaluator import LLMEvaluator
from email_sender import EmailSender


def main(config_path: str = "config.yaml"):
    """
    Run the daily arxiv digest workflow.
    
    Args:
        config_path: Path to configuration file
    """
    print("=" * 70)
    print("ArXiv Daily Digest - Starting...")
    print("=" * 70)
    print()
    
    # Step 1: Load configuration
    print("Loading configuration...")
    try:
        config = ConfigParser(config_path)
    except Exception as e:
        print(f"Error loading config: {e}")
        return 1
    
    # Step 2: Parse Zotero library
    print("Parsing Zotero library...")
    zotero_config = config.get_zotero_config()
    library_file = zotero_config.get('library_file', '')
    
    if library_file and Path(library_file).exists():
        zotero = ZoteroParser(library_file)
        research_context = zotero.get_summary()
        print(
            f"  Found {len(zotero.get_papers())} papers "
            "in library"
        )
    else:
        print(
            "  No Zotero library found, "
            "using interests only"
        )
        research_context = "No prior research library provided."
    
    # Step 3: Fetch papers from ArXiv
    print("\nFetching papers from ArXiv...")
    arxiv_config = config.get_arxiv_config()
    
    arxiv_client = ArxivClient(
        categories=arxiv_config['categories'],
        keywords=arxiv_config.get('keywords', []),
        max_days_back=arxiv_config.get('max_days_back', 1)
    )
    
    papers = arxiv_client.fetch_papers()
    print(
        f"  Found {len(papers)} papers "
        "(after filtering)"
    )
    
    if not papers:
        print("\nNo papers found. Exiting.")
        return 0
    
    # Step 4: Evaluate papers with LLM
    print("\nEvaluating papers for relevance...")
    openai_config = config.get_openai_config()
    interests_config = config.get_interests()
    
    evaluator = LLMEvaluator(
        api_key=openai_config['api_key'],
        model=openai_config.get('model', 'gpt-4o-mini'),
        threshold=openai_config.get('threshold', 7.0),
        max_workers=openai_config.get('max_workers', 10)
    )
    
    user_interests = interests_config.get(
        'description', 
        ''
    )
    
    relevant_papers = evaluator.evaluate_papers(
        papers=papers,
        research_context=research_context,
        user_interests=user_interests
    )
    
    print(
        f"  Found {len(relevant_papers)} relevant papers "
        f"(score >= {evaluator.threshold})"
    )
    
    # Step 5: Send email digest (even if no papers found)
    print("\nSending email digest...")
    email_config = config.get_email_config()
    
    sender = EmailSender(
        smtp_server=email_config['smtp_server'],
        smtp_port=email_config['smtp_port'],
        from_email=email_config['from_email'],
        password=email_config['password'],
        to_email=email_config['to_email']
    )
    
    success = sender.send_digest(relevant_papers)
    
    if success:
        print("\n" + "=" * 70)
        print("Digest completed successfully!")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("Digest completed with errors.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    config_file = sys.argv[1] if len(
        sys.argv
    ) > 1 else "config.yaml"
    
    exit_code = main(config_file)
    sys.exit(exit_code)

