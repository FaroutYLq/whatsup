"""
LLM-based paper relevance evaluator using the Anthropic (Claude) API
"""

from anthropic import Anthropic
from anthropic import AuthenticationError, PermissionDeniedError, RateLimitError
from typing import Dict, Any, List, Tuple
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


# Errors that mean the whole run is broken (bad/deactivated API key,
# revoked permissions). These must abort the digest, not be swallowed
# per-paper — otherwise the run silently produces an empty digest.
FATAL_API_ERRORS = (AuthenticationError, PermissionDeniedError)

# Default Claude model — fast + cheap, well suited to high-volume
# relevance scoring.
DEFAULT_MODEL = "claude-haiku-4-5"

# Structured-output tool. Forcing the model to call this eliminates the
# regex parsing that previously turned any unparseable response into a
# silent score of 0.0 (i.e. a dropped paper).
RELEVANCE_TOOL = {
    "name": "record_relevance",
    "description": (
        "Record the relevance of the paper to the user's research "
        "interests."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "score": {
                "type": "number",
                "description": (
                    "Relevance on a 0-10 scale. 0-3: not relevant, "
                    "4-6: somewhat relevant, 7-8: relevant, "
                    "9-10: highly relevant."
                ),
            },
            "reason": {
                "type": "string",
                "description": "One-sentence explanation of the score.",
            },
        },
        "required": ["score", "reason"],
    },
}


class FatalEvaluationError(RuntimeError):
    """Raised when the LLM cannot be reached at all (e.g. invalid key)."""


class LLMEvaluator:
    """Evaluate paper relevance using Anthropic's Claude models."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        threshold: float = 7.0,
        max_workers: int = 10,
        verbose: bool = False
    ):
        """
        Initialize the LLM evaluator.

        Args:
            api_key: Anthropic API key
            model: Claude model to use (e.g. claude-haiku-4-5)
            threshold: Minimum score for relevance (0-10)
            max_workers: Max parallel API calls
            verbose: Show sample LLM responses
        """
        self.client = Anthropic(api_key=api_key)

        # Guard against a stale/non-Claude model string (e.g. an
        # OpenAI 'gpt-4o' left over in config) being sent to the
        # Anthropic API. Fall back to Haiku instead of erroring.
        if not str(model).startswith("claude-"):
            print(
                f"  Warning: model '{model}' is not a Claude model; "
                f"falling back to {DEFAULT_MODEL}."
            )
            model = DEFAULT_MODEL
        self.model = model
        self.threshold = threshold
        self.max_workers = max_workers
        self.verbose = verbose
        self.sample_count = 0

    def validate_credentials(self) -> None:
        """
        Make one tiny call to confirm the API key works.

        Raises:
            FatalEvaluationError: if the key is invalid/deactivated or
                permissions were revoked. This aborts the whole run.
        """
        try:
            self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
        except FATAL_API_ERRORS as e:
            raise FatalEvaluationError(
                "Anthropic API key rejected — the key is invalid, "
                "deactivated, or lacks permission for model "
                f"'{self.model}'. Update your API key and retry. "
                f"(Original error: {e})"
            ) from e

    def _build_system_blocks(
        self,
        research_context: str,
        user_interests: str
    ) -> List[Dict[str, Any]]:
        """
        Build the cached system prompt.

        The research background + interests are identical for every
        paper in a run, so we mark them with cache_control. Anthropic
        prompt caching then charges the (potentially large) Zotero
        context once per ~5 minutes instead of on every paper, cutting
        evaluation cost substantially for parallel runs.
        """
        return [
            {
                "type": "text",
                "text": (
                    "You are an academic research assistant. Evaluate "
                    "how relevant each arXiv paper is to the user's "
                    "research background and current interests, then "
                    "call the record_relevance tool with a 0-10 score "
                    "and a one-sentence reason."
                ),
            },
            {
                "type": "text",
                "text": (
                    f"RESEARCH BACKGROUND:\n{research_context}\n\n"
                    f"CURRENT SPECIFIC INTERESTS:\n{user_interests}"
                ),
                "cache_control": {"type": "ephemeral"},
            },
        ]

    def evaluate_papers(
        self,
        papers: List[Dict[str, Any]],
        research_context: str,
        user_interests: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Evaluate multiple papers for relevance in parallel.

        Args:
            papers: List of paper dictionaries
            research_context: Summary from Zotero library
            user_interests: User's interest description

        Returns:
            (relevant_papers, unscored_papers). unscored_papers are
            papers that could not be evaluated (rate limits, transient
            errors) — surfaced separately so a relevant paper that hit a
            bad API minute is never silently discarded as irrelevant.
        """
        # Fail fast on a broken key instead of silently emailing an
        # empty digest after every paper errors out.
        self.validate_credentials()

        system_blocks = self._build_system_blocks(
            research_context, user_interests
        )

        relevant_papers = []
        unscored_papers = []

        # Parallel evaluation with progress bar
        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # Submit all evaluation tasks
            future_to_paper = {
                executor.submit(
                    self._evaluate_single_paper,
                    paper,
                    system_blocks
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

                        if result['status'] == 'failed':
                            # Could not evaluate — keep it, don't drop it.
                            paper['eval_error'] = result['reason']
                            unscored_papers.append(paper)
                        elif result['score'] >= self.threshold:
                            paper['relevance_score'] = result['score']
                            paper['relevance_reason'] = result['reason']
                            relevant_papers.append(paper)
                        # else: genuinely below threshold — dropped.
                    except FatalEvaluationError:
                        # Key died mid-run — abort instead of
                        # continuing to a silently empty digest.
                        raise
                    except Exception as e:
                        # Unexpected failure in our own handling — treat
                        # as unscored rather than losing the paper.
                        print(
                            f"\nError processing paper "
                            f"'{paper['title'][:50]}...': {e}"
                        )
                        paper['eval_error'] = f"Processing error: {e}"
                        unscored_papers.append(paper)
                    finally:
                        pbar.update(1)

        # Sort by relevance score (highest first)
        relevant_papers.sort(
            key=lambda x: x['relevance_score'],
            reverse=True
        )

        return relevant_papers, unscored_papers

    def _evaluate_single_paper(
        self,
        paper: Dict[str, Any],
        system_blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate a single paper.

        Args:
            paper: Paper dictionary
            system_blocks: Cached system prompt blocks

        Returns:
            Dict with 'status' ('ok' or 'failed'), plus 'score' and
            'reason'. A 'failed' status means the paper could not be
            evaluated and should be surfaced as unscored, NOT scored 0.
        """
        prompt = self._build_prompt(paper)

        # Retry logic for rate limits (the SDK also retries internally,
        # this adds extra headroom for long parallel runs).
        max_retries = 5
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=256,
                    system=system_blocks,
                    tools=[RELEVANCE_TOOL],
                    tool_choice={
                        "type": "tool",
                        "name": "record_relevance",
                    },
                    messages=[{"role": "user", "content": prompt}],
                )

                score, reason = self._extract_tool_result(response)

                if self.verbose and self.sample_count < 3:
                    self.sample_count += 1
                    print(
                        f"\n{'='*60}\n"
                        f"Sample Response {self.sample_count}:\n"
                        f"Paper: {paper['title'][:50]}...\n"
                        f"Parsed Score: {score}\n"
                        f"Parsed Reason: {reason}\n"
                        f"{'='*60}\n"
                    )

                return {
                    'status': 'ok',
                    'score': score,
                    'reason': reason,
                }

            except FATAL_API_ERRORS as e:
                # Invalid/deactivated key or revoked permission — this
                # affects every paper, so abort the whole run.
                raise FatalEvaluationError(
                    "Anthropic API key rejected during evaluation — "
                    "the key is invalid, deactivated, or lacks "
                    f"permission. (Original error: {e})"
                ) from e
            except RateLimitError:
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    import random
                    delay = base_delay * (2 ** attempt)
                    delay += random.uniform(0, 1)
                    time.sleep(delay)
                    continue
                # Exhausted retries — mark unscored, do NOT drop.
                return {
                    'status': 'failed',
                    'score': 0.0,
                    'reason': 'Rate limit exceeded after retries',
                }
            except Exception as e:
                # Other transient/per-paper errors — mark unscored so a
                # possibly relevant paper is surfaced, not silently lost.
                print(
                    f"Error evaluating paper "
                    f"'{paper['title'][:50]}...': {e}"
                )
                return {
                    'status': 'failed',
                    'score': 0.0,
                    'reason': f'Evaluation error: {e}',
                }

        return {
            'status': 'failed',
            'score': 0.0,
            'reason': 'Max retries exceeded',
        }

    def _extract_tool_result(self, response) -> Tuple[float, str]:
        """
        Pull the score/reason from the forced tool call.

        Raises:
            ValueError: if no valid tool call is present (caught by the
                caller and reported as an evaluation failure).
        """
        for block in response.content:
            if (
                getattr(block, "type", None) == "tool_use"
                and block.name == "record_relevance"
            ):
                data = block.input or {}
                raw_score = data.get("score")
                if raw_score is None:
                    raise ValueError("Tool call missing 'score'")
                # Clamp to the valid range in case the model overshoots.
                score = max(0.0, min(10.0, float(raw_score)))
                reason = data.get("reason", "No reason provided")
                return score, reason

        raise ValueError("Model did not return a record_relevance call")

    def _build_prompt(self, paper: Dict[str, Any]) -> str:
        """Build the per-paper user message."""
        return (
            "Evaluate the relevance of this new arXiv paper to the "
            "research background and interests above, then call "
            "record_relevance.\n\n"
            f"Title: {paper['title']}\n"
            f"Abstract: {paper['abstract']}"
        )
