# ArXiv Daily Digest

Get one email per day with arXiv papers that match your interests.

This project pulls recent arXiv papers, optionally uses your Zotero library as context, scores papers with an OpenAI model, and sends only the relevant ones to your inbox.

## Core Use Case

Use this if you want to:
- Track a few arXiv categories every day
- Filter down to papers that fit your research goals
- Receive a short digest email instead of checking arXiv manually

## Key Features

- Category + keyword pre-filtering (faster, cheaper)
- LLM-based relevance scoring (0-10)
- Optional Zotero context for personalization
- Email digest delivery
- Daily automation via cron/launchd

## Quick Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create your config:
```bash
cp config.yaml.example config.yaml
```

3. Edit `config.yaml` with:
- OpenAI API key
- SMTP email settings
- arXiv categories
- keywords
- interest description
- Zotero export path (optional)

4. Run once to test:
```bash
python src/main.py
```

5. (Optional) Schedule daily runs:
- See [docs/CRON_SETUP.md](docs/CRON_SETUP.md)

## Adapt It For Yourself

Use this checklist to tune relevance and cost quickly:

1. Pick 1-3 arXiv categories you actually read.
2. Add 5-20 specific keywords from your domain.
3. Rewrite the interest description around your current projects.
4. Set threshold:
- `6.0` for broader discovery
- `7.0` for balanced output
- `8.0+` for high precision only
5. Start with `max_days_back: 1`.
6. If too many papers appear, narrow categories/keywords first, then raise threshold.
7. If too few papers appear, lower threshold or broaden keywords.

Template example:
```yaml
arxiv:
  categories: ["cond-mat.supr-con", "quant-ph"]
  keywords: ["quasiparticle", "single-photon detector", "mkid"]
  max_days_back: 1

interests:
  description: |
    I care about superconducting detectors and quasiparticle dynamics,
    with emphasis on device physics and readout methods.

evaluation:
  relevance_threshold: 7.0
```

## Run Options

- Default config:
```bash
python src/main.py
```

- Custom config path:
```bash
python src/main.py /path/to/config.yaml
```

## Docs

- [docs/ZOTERO_EXPORT.md](docs/ZOTERO_EXPORT.md)
- [docs/GMAIL_SETUP.md](docs/GMAIL_SETUP.md)
- [docs/CRON_SETUP.md](docs/CRON_SETUP.md)

## Troubleshooting

- No papers found: broaden categories/keywords, check `max_days_back`
- No relevant papers: lower threshold, improve interest description
- No email received: recheck SMTP settings and spam folder
