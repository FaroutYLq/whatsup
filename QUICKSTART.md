# Quick Start Guide

Get your ArXiv Daily Digest running in 5 minutes!

## Prerequisites

- Python 3.7+
- Anthropic (Claude) API key
- Gmail account with app password

## 5-Minute Setup

### 1. Install Dependencies

```bash
cd /Users/lanqingyuan/Documents/GitHub/whatsup
./setup.sh
```

Or manually:

```bash
pip install -r requirements.txt
cp config.yaml.example config.yaml
```

### 2. Get Your API Keys

**Anthropic (Claude) API Key:**
1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key (starts with `sk-ant-`)
3. Copy it (you can only see it once)

**Gmail App Password:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Factor Authentication
3. Create App Password for "Mail"
4. Copy the 16-character password

### 3. Configure

Edit `config.yaml`:

```bash
nano config.yaml
```

Minimal required changes:

```yaml
email:
  from_email: your.email@gmail.com
  password: your-16-char-app-password
  to_email: your.email@gmail.com

anthropic:
  api_key: sk-ant-your-anthropic-key-here

arxiv:
  categories:
    - cond-mat.supr-con  # Change to your field
  keywords:
    - superconductor     # Change to your topics

zotero:
  library_file: ""  # Optional - leave empty for now

interests:
  description: |
    I'm interested in:
    1. Your specific research area
    2. Your current topics
```

### 4. Run First Test

```bash
python src/main.py
```

You should receive an email with relevant papers!

### 5. Automate (Optional)

Run daily at 8 AM:

```bash
crontab -e
```

Add this line (update the path):

```
0 8 * * * /Users/lanqingyuan/Documents/GitHub/whatsup/run_digest.sh
```

## Troubleshooting Quick Fixes

**"No papers found"**
- Use broader categories or remove keywords temporarily

**"Email not sent"**
- Check Gmail app password (no spaces)
- Verify SMTP settings: `smtp.gmail.com:587`

**"Anthropic API key rejected" / API error**
- Check the API key is correct (starts with `sk-ant-`)
- Verify you have credits:
  https://console.anthropic.com/settings/billing

**"Config file not found"**
- Run from project directory
- Or: `python src/main.py /full/path/to/config.yaml`

## What's Next?

### Add Your Zotero Library

For better recommendations:

1. Export your Zotero library as BibTeX
   (File → Export Library → BibTeX)
2. Update `config.yaml`:
   ```yaml
   zotero:
     library_file: /path/to/your/library.bib
   ```

See [docs/ZOTERO_EXPORT.md](docs/ZOTERO_EXPORT.md) 
for details.

### Fine-Tune Settings

Adjust in `config.yaml`:

- **More papers**: Lower `threshold` to 6.0
- **Fewer papers**: Raise `threshold` to 8.0
- **Save money**: Add specific `keywords` for pre-filter
- **More categories**: Add to `categories` list

### Monitor Costs

Check Anthropic usage:
https://console.anthropic.com/settings/usage

Typical cost: **~$1-2/month** with claude-haiku-4-5

## Get Help

- **Full docs**: [README.md](README.md)
- **Gmail setup**: [docs/GMAIL_SETUP.md](docs/GMAIL_SETUP.md)
- **Zotero export**: [docs/ZOTERO_EXPORT.md](docs/ZOTERO_EXPORT.md)
- **Automation**: [docs/CRON_SETUP.md](docs/CRON_SETUP.md)

---

**You're all set! Enjoy your personalized arXiv digest! 🎉**

