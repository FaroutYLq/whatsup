"""
LLM-based paper relevance evaluator using OpenAI API
"""

from openai import OpenAI
from typing import Dict, Any, List
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class LLMEvaluator:
    """Evaluate paper relevance using OpenAI's GPT models."""
    
    def __init__(
        self, 
        api_key: str,
        model: str = "gpt-4o-mini",
        threshold: float = 7.0,
        max_workers: int = 10,
        verbose: bool = False
    ):
        """
        Initialize the LLM evaluator.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (e.g., gpt-4o-mini)
            threshold: Minimum score for relevance (0-10)
            max_workers: Max parallel API calls
            verbose: Show sample LLM responses
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.threshold = threshold
        self.max_workers = max_workers
        self.verbose = verbose
        self.sample_count = 0
    
    def evaluate_papers(
        self,
        papers: List[Dict[str, Any]],
        research_context: str,
        user_interests: str
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple papers for relevance in parallel.
        
        Args:
            papers: List of paper dictionaries
            research_context: Summary from Zotero library
            user_interests: User's interest description
            
        Returns:
            List of relevant papers with scores
        """
        relevant_papers = []
        
        # Parallel evaluation with progress bar
        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # Submit all evaluation tasks
            future_to_paper = {
                executor.submit(
                    self._evaluate_single_paper,
                    paper,
                    research_context,
                    user_interests
                ): paper
                for paper in papers
            }
            
            # Process completed tasks with progress bar
            with tqdm(
                total=len(papers),
                desc="Evaluating papers",
                unit="paper"
            ) as pbar:
                for future in as_completed(future_to_paper):
                    paper = future_to_paper[future]
                    try:
                        result = future.result()
                        
                        if result['score'] >= self.threshold:
                            paper['relevance_score'] = (
                                result['score']
                            )
                            paper['relevance_reason'] = (
                                result['reason']
                            )
                            relevant_papers.append(paper)
                    except Exception as e:
                        print(
                            f"\nError processing paper "
                            f"'{paper['title'][:50]}...': {e}"
                        )
                    finally:
                        pbar.update(1)
        
        # Sort by relevance score (highest first)
        relevant_papers.sort(
            key=lambda x: x['relevance_score'], 
            reverse=True
        )
        
        return relevant_papers
    
    def _evaluate_single_paper(
        self,
        paper: Dict[str, Any],
        research_context: str,
        user_interests: str
    ) -> Dict[str, Any]:
        """
        Evaluate a single paper.
        
        Args:
            paper: Paper dictionary
            research_context: Summary from Zotero library
            user_interests: User's interest description
            
        Returns:
            Dictionary with score and reason
        """
        prompt = self._build_prompt(
            paper, research_context, user_interests
        )
        
        # Retry logic for rate limits
        max_retries = 5
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an academic research "
                                "assistant. Evaluate the "
                                "relevance of papers to the "
                                "user's research interests."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_completion_tokens=200
                )
                
                content = response.choices[0].message.content
                score, reason = self._parse_response(
                    content, paper['title']
                )
                
                # Show first 3 responses if verbose
                if self.verbose and self.sample_count < 3:
                    self.sample_count += 1
                    print(
                        f"\n{'='*60}\n"
                        f"Sample Response {self.sample_count}:\n"
                        f"Paper: {paper['title'][:50]}...\n"
                        f"LLM Response:\n{content}\n"
                        f"Parsed Score: {score}\n"
                        f"Parsed Reason: {reason}\n"
                        f"{'='*60}\n"
                    )
                
                return {'score': score, 'reason': reason}
                
            except Exception as e:
                error_str = str(e)
                
                # Handle rate limit errors
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        delay = base_delay * (2 ** attempt)
                        # Add jitter
                        import random
                        delay += random.uniform(0, 1)
                        time.sleep(delay)
                        continue
                    else:
                        return {
                            'score': 0.0,
                            'reason': 'Rate limit exceeded'
                        }
                
                # Other errors
                print(
                    f"Error evaluating paper "
                    f"'{paper['title'][:50]}...': {e}"
                )
                return {
                    'score': 0.0, 
                    'reason': 'Evaluation error'
                }
        
        return {'score': 0.0, 'reason': 'Max retries exceeded'}
    
    def _build_prompt(
        self,
        paper: Dict[str, Any],
        research_context: str,
        user_interests: str
    ) -> str:
        """Build the evaluation prompt."""
        prompt = f"""Given the following research background 
and interests, evaluate the relevance of this new arXiv paper.

{research_context}

CURRENT SPECIFIC INTERESTS:
{user_interests}

NEW PAPER TO EVALUATE:
Title: {paper['title']}
Abstract: {paper['abstract']}

Rate the relevance of this paper on a scale of 0-10:
- 0-3: Not relevant
- 4-6: Somewhat relevant
- 7-8: Relevant
- 9-10: Highly relevant

Respond in the format:
SCORE: [0-10]
REASON: [One sentence explanation]"""
        
        return prompt
    
    def _parse_response(
        self, 
        content: str, 
        paper_title: str = ""
    ) -> tuple:
        """
        Parse LLM response to extract score and reason.
        
        Args:
            content: LLM response text
            paper_title: Paper title for debug logging
            
        Returns:
            Tuple of (score, reason)
        """
        import re
        
        score = 0.0
        reason = "No reason provided"
        
        # Try multiple parsing strategies
        
        # Strategy 1: Look for "SCORE:" pattern
        score_match = re.search(
            r'SCORE:\s*(\d+\.?\d*)', 
            content, 
            re.IGNORECASE
        )
        if score_match:
            score = float(score_match.group(1))
        else:
            # Strategy 2: Look for any score pattern
            # like "Score: 8" or "rating: 7/10"
            alt_match = re.search(
                r'(?:score|rating)[\s:]+(\d+\.?\d*)',
                content,
                re.IGNORECASE
            )
            if alt_match:
                score = float(alt_match.group(1))
            else:
                # Strategy 3: Just find first number 0-10
                num_match = re.search(
                    r'\b([0-9]|10)(?:\.\d+)?\b', 
                    content
                )
                if num_match:
                    potential_score = float(num_match.group(1))
                    if 0 <= potential_score <= 10:
                        score = potential_score
        
        # Extract reason
        reason_match = re.search(
            r'REASON:\s*(.+?)(?:\n|$)', 
            content, 
            re.IGNORECASE | re.DOTALL
        )
        if reason_match:
            reason = reason_match.group(1).strip()
        else:
            # Fallback: use first sentence
            sentences = re.split(r'[.!?]\s+', content)
            if len(sentences) > 1:
                reason = sentences[1][:100]
            else:
                reason = content[:100]
        
        # Debug: Log first few responses
        if score == 0.0:
            print(
                f"\n[DEBUG] Failed to parse score for: "
                f"{paper_title}..."
            )
            print(f"[DEBUG] LLM response: {content}")
        
        return score, reason

