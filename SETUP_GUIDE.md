# AI × Fintech × Retail Intelligence Digest — Setup Guide

A tool that automatically fetches, filters, summarises, and emails you daily
news about AI developments in consumer banking and fintech.

---

## Files in this project

| File | Purpose |
|------|---------|
| `main.py` | Entry point — run this to fetch news and send digest |
| `config.py` | All settings (no secrets — reads from env vars) |
| `fetcher.py` | Fetches RSS feeds, scores articles for relevance |
| `web_searcher.py` | Perplexity web search for non-RSS articles |
| `summarizer.py` | Claude-powered bullet-point summarisation |
| `digest_builder.py` | Builds the HTML + plain-text email |
| `email_sender.py` | Sends via Gmail SMTP |
| `requirements.txt` | Python dependencies |
| `.github/workflows/digest.yml` | GitHub Actions cron job |

---

## Option A — GitHub Actions (recommended, runs automatically)

### Step 1 — Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 2 — Add repository secrets

Go to your repo on GitHub → **Settings → Secrets and variables → Actions → New repository secret**

Add these five secrets:

| Secret name | Value |
|-------------|-------|
| `EMAIL_SENDER` | Your Gmail address |
| `EMAIL_PASSWORD` | Gmail App Password (see below) |
| `EMAIL_RECIPIENTS` | Comma-separated list, e.g. `a@b.com,c@d.com` |
| `PERPLEXITY_API_KEY` | From https://www.perplexity.ai/settings/api |
| `ANTHROPIC_API_KEY` | From https://console.anthropic.com/ |

**Getting a Gmail App Password:**
1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Select "Mail" → your device
3. Copy the 16-character password generated (spaces are fine to include)

### Step 3 — Done

The digest will run automatically **Monday–Friday at 07:00 UTC**.

To trigger it manually: **Actions tab → Daily AI Banking Digest → Run workflow**.

The HTML preview is saved as a workflow artifact after every run — download it
from the run page to inspect the digest visually.

---

## Option B — Run locally

### Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Export secrets in your shell

```bash
export EMAIL_SENDER="you@gmail.com"
export EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"
export EMAIL_RECIPIENTS="you@gmail.com,colleague@work.com"
export PERPLEXITY_API_KEY="pplx-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or create a `.env` file (already in `.gitignore`) and load it with:

```bash
set -a; source .env; set +a
```

### Step 3 — Run

```bash
# Preview the digest (HTML saved, no email sent):
python3 main.py --preview

# Send the real digest email:
python3 main.py

# Test with sample data (no network or API calls needed):
python3 main.py --test

# Check all RSS feeds are reachable:
python3 main.py --validate
```

---

## Changing the schedule

Edit `.github/workflows/digest.yml`:

```yaml
schedule:
  - cron: "0 7 * * 1-5"   # Mon–Fri 07:00 UTC  ← change this
```

Cron reference: `minute hour day-of-month month day-of-week`
- `"0 7 * * *"` — every day at 07:00 UTC
- `"0 6 * * 1"` — every Monday at 06:00 UTC

---

## Tuning the digest

All settings are in `config.py`:

| Setting | Default | Effect |
|---------|---------|--------|
| `LOOKBACK_HOURS` | 48 | How far back to look for articles |
| `MIN_RELEVANCE_SCORE` | 2 | Lower = more articles; raise to reduce noise |
| `MAX_ARTICLES_IN_DIGEST` | 40 | Cap on primary articles |
| `REQUIRE_AI_AND_BANKING` | True | Must match AI *and* banking keywords |
| `ENABLE_WEB_SEARCH` | True | Perplexity searches for non-RSS news |
| `ENABLE_SUMMARIZATION` | True | Claude bullet-point summaries |

RSS feeds and keyword lists are also in `config.py` — add or remove freely.
