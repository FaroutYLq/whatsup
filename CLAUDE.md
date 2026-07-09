# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ArXiv Weekly Digest — a Python tool that fetches recent arXiv papers, scores them for relevance using an Anthropic (Claude) LLM, and emails a weekly digest. Optionally uses a Zotero library export as context for personalized scoring.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the digest (default config.yaml)
python src/main.py

# Run with custom config
python src/main.py /path/to/config.yaml

# Run via shell wrapper (logs to digest.log)
./run_digest.sh

# First-time setup
./setup.sh
```

There are no tests or linting configured in this project.

## Architecture

The pipeline is orchestrated by `src/main.py` and runs sequentially:

1. **ConfigParser** (`src/config_parser.py`) — Loads and validates `config.yaml` (YAML with sections: email, arxiv, anthropic, zotero, interests).
2. **ZoteroParser** (`src/zotero_parser.py`) — Parses a `.bib` or `.json` Zotero export to build research context for the LLM prompt.
3. **ArxivClient** (`src/arxiv_client.py`) — Queries the arXiv API by category using the modern `arxiv.Client` (built-in retry/backoff). Sorts and filters by `lastUpdatedDate` (so cross-lists and late announcements aren't missed), paginates until it crosses the `max_days_back` cutoff (full window coverage, not a fixed 100-result cap), and deduplicates by versionless arXiv id. Keyword filtering is an optional cost-saver (`keyword_filter`, default off; whole-word match). Returns `(papers, failed_categories)` — a category that fails after retries is reported, not silently dropped.
4. **LLMEvaluator** (`src/llm_evaluator.py`) — Sends each paper to Anthropic/Claude (parallel via ThreadPoolExecutor) with the user's interests + Zotero context in a cached system prompt (prompt caching cuts token cost). Uses forced tool use (`record_relevance`) for a structured `{score, reason}` — no regex parsing. Retries rate limits with exponential backoff, aborts the whole run if the API key is rejected, and returns `(relevant_papers, unscored_papers)` so papers that error out during scoring are surfaced for manual review instead of silently discarded as irrelevant.
5. **EmailSender** (`src/email_sender.py`) — Formats results as plain-text email and sends via SMTP/TLS with retry/backoff. The body includes a coverage-warning banner (failed categories / unscored papers) and a "could not evaluate" section.

## Configuration

- `config.yaml` (git-ignored) holds all runtime settings: SMTP credentials, Anthropic API key, arXiv categories/keywords, Zotero path, interests description, and relevance threshold.
- `config.yaml.example` is the template.
- Required config sections: `email`, `arxiv`, `anthropic`, `zotero`, `interests`.

## CI/CD

GitHub Actions workflow (`.github/workflows/digest-every-3-days.yml`, now runs weekly — filename kept for stable workflow identity):
- Runs weekly, targeting Thursday 17:00 America/Chicago. Because GitHub cron is UTC-only and ignores DST, it fires at both 22:00 and 23:00 UTC Thursday (`cron: "0 22 * * 4"` / `"0 23 * * 4"`) and a guard step keeps only the fire where Chicago local time is 17:00 — exactly one run per Thursday year-round.
- A keepalive step (`gautamkrishnar/keepalive-workflow`) runs on schedule events to prevent GitHub from disabling the cron after 60 days of repo inactivity. Requires `contents: write` permission.
- Set `arxiv.max_days_back` to 7 so each weekly run covers the full week since the previous one.
- Config is injected from the `WHATSUP_CONFIG_YAML` secret.
- Zotero library is stored as gzipped base64 chunks across multiple secrets (`WHATSUP_ZOTERO_BIB_GZ_B64_01` through `_12`).
- Can be triggered manually via `workflow_dispatch`.

## Key Details

- All source lives in `src/` with no package structure — modules import each other directly (run from `src/` or project root with `python src/main.py`).
- Python 3.11 is used in CI.
- The `arxiv` library (v2.1.0) is used for arXiv API access.
- LLM evaluation uses the `anthropic` SDK with configurable model (default: `claude-haiku-4-5`) and parallel workers (default: 10).
