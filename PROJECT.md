# Banking AI Intelligence Digest — Project Overview

## What is this?

A fully automated daily email newsletter that monitors the internet for news about **artificial intelligence in consumer banking and fintech**, filters out the noise, summarises the best stories using AI, and delivers a ranked digest to your inbox every weekday morning — without you lifting a finger.

---

## The problem it solves

AI in banking is moving fast. Relevant news is scattered across dozens of sources — fintech blogs, regulatory announcements, paywalled trade publications, AI research labs, and startup press releases. Reading everything manually takes hours and you still miss things.

This tool does it all automatically. It knows what's relevant to someone working at a consumer bank, and it ignores everything else.

---

## How it works — the full pipeline

```
Every weekday at 07:00 UTC (08:00 London / 03:00 New York)
         │
         ▼
  ① COLLECT
     Pull the last 48 hours of articles from 22 curated RSS feeds
     across AI, fintech, banking, and regulatory sources.
     ~150 raw articles gathered per run.
         │
         ▼
  ② SEARCH
     Ask Perplexity AI to run 4 targeted web searches — e.g.
     "AI in retail banking product launches last 48 hours" —
     to catch stories that aren't in any RSS feed (paywalled
     articles, startup announcements, regulatory notices).
     Adds ~5–10 additional stories per run.
         │
         ▼
  ③ FILTER
     Every article is scored against three keyword lists:
     AI keywords, Fintech keywords, and Retail Banking keywords.

     • PRIMARY story   = matches AI keywords AND banking/fintech keywords
     • SECONDARY story = matches any keywords but not the AI+banking crossover
     • Discarded       = no relevant keyword matches

     Typically ~15–20 primary stories and ~30 secondary stories survive.
         │
         ▼
  ④ RANK
     Primary stories are sorted by relevance score — the article
     with the most keyword matches appears first.
         │
         ▼
  ⑤ SUMMARISE
     Each primary article is sent to Claude AI (Anthropic), which
     reads the title and raw text and writes 3–5 crisp bullet points:
     • Key facts (what happened, who, numbers)
     • Why it matters for a consumer bank
     Secondary articles are NOT summarised — just links and snippets.
         │
         ▼
  ⑥ BUILD
     An HTML email is assembled:
     • A stats header (article counts, date)
     • Primary section: ranked cards with AI summaries and relevance badges
     • Secondary section: compact link list for broader awareness
         │
         ▼
  ⑦ SEND
     The digest is emailed via Gmail to all configured recipients.
```

---

## News sources monitored (22 feeds)

| Category | Sources |
|----------|---------|
| **AI & Technology** | VentureBeat AI, TechCrunch AI, MIT Technology Review, The Verge AI, Wired, AI Business, OpenAI Blog, HuggingFace Blog |
| **Fintech Specialist** | Finextra, PYMNTS, Fintech Futures, Tearsheet, The Fintech Times, Finovate, Fintech Nexus |
| **Banking & Consumer Finance** | The Financial Brand, Banking Dive, American Banker, Crowdfund Insider, CFPB Blog |
| **Regulatory** | OCC (US Office of the Comptroller), FCA (UK Financial Conduct Authority) |

> Some sources that block direct RSS access (e.g. American Banker, Financial Brand) are proxied through Google News search to retrieve their headlines.

---

## The two AI layers

### Perplexity — Web Search Agent
**What it does:** Given a search question, Perplexity scours the live web and returns sourced news stories with real article URLs.

**Why it's needed:** RSS feeds only cover publications that publish feeds. A lot of banking AI news lives in press releases, regulatory PDFs, and paywalled articles that never appear in an RSS feed. Perplexity finds these.

**4 daily search queries run:**
1. AI / machine learning consumer banking product launches (last 48 hours)
2. AI fraud detection, credit scoring, digital banking news
3. Generative AI / LLM chatbot deployments in banking (mortgage, loans, customer service)
4. AI banking regulation — CFPB, FCA, OCC compliance announcements

### Claude (Anthropic Haiku) — Summarisation
**What it does:** Reads a news article's title and raw text, and writes 3–5 focused bullet points — specific facts, company names, numbers, and a final bullet on why it matters for a consumer bank.

**Why it's needed:** Raw RSS summaries are often truncated, promotional, or padded. Claude extracts only the substance that a banking professional actually needs to know.

---

## How the relevance filter works

Three keyword groups are matched against every article's title and summary:

- **AI keywords** — terms like `machine learning`, `large language model`, `generative AI`, `fraud detection`, `credit scoring`, `AI agent`, `chatbot` (35+ terms)
- **Fintech keywords** — terms like `digital bank`, `payments`, `neobank`, `open banking`, `core banking`, `loan origination`, `challenger bank` (30+ terms)
- **Retail Banking keywords** — terms like `mortgage`, `savings account`, `mobile banking`, `personal finance`, `customer onboarding`, `PFM`, `next best action` (35+ terms)

An article must score at least one AI match **and** at least one fintech/retail banking match to become a **primary story**. This crossover requirement keeps the digest focused on AI *applied to* banking, not generic tech news or generic banking news.

---

## What the digest looks like

**Primary section** — up to 40 AI × banking stories, ranked by relevance:
- 🔥 **Must-Read** badge for highest-scoring stories
- ⭐ **Top Story** badge for strong matches
- Article title, source name, publication date
- 3–5 AI-generated bullet points
- "Read full article →" link

**Secondary section** — "Also in the News" — up to 30 broader stories:
- Compact rows: title + source + date + raw 180-character snippet
- No AI summary (keeps it lightweight)
- Link to full article

---

## Credentials required (5 total)

| Credential | What it is | Where to get it |
|------------|-----------|----------------|
| `EMAIL_SENDER` | Gmail address used to send the digest | Your Gmail account |
| `EMAIL_PASSWORD` | Gmail App Password (not your login password) | [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) — requires 2-Step Verification |
| `EMAIL_RECIPIENTS` | Comma-separated list of recipient emails | e.g. `you@gmail.com,colleague@work.com` |
| `PERPLEXITY_API_KEY` | Perplexity API key | [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api) |
| `ANTHROPIC_API_KEY` | Anthropic (Claude) API key | [console.anthropic.com](https://console.anthropic.com) |

In GitHub Actions these are stored as **repository secrets** (Settings → Secrets and variables → Actions). No credentials ever appear in the code.

---

## Automation

The digest runs automatically via **GitHub Actions** — no server, no infrastructure to maintain.

- **Schedule:** Monday–Friday at 07:00 UTC
- **Manual trigger:** Actions tab → Daily AI Banking Digest → Run workflow
- **Preview mode:** Generates the HTML digest without sending email (useful for testing)
- **Artifact:** The HTML preview is saved after every run and downloadable from the Actions run page for 7 days

---

## Project files at a glance

| File | Role |
|------|------|
| `main.py` | Orchestrates the full pipeline — collect → search → filter → rank → summarise → build → send |
| `config.py` | All settings: feed list, keyword lists, Perplexity queries, feature flags. Reads secrets from environment variables |
| `fetcher.py` | Fetches RSS feeds, scores articles by keyword, deduplicates URLs, returns primary and secondary article lists |
| `web_searcher.py` | Calls Perplexity API, parses numbered story blocks, maps stories to citation URLs |
| `summarizer.py` | Calls Claude Haiku API, generates bullet-point summaries for primary articles |
| `digest_builder.py` | Assembles the HTML and plain-text email from the ranked article lists |
| `email_sender.py` | Sends the finished email via Gmail SMTP |
| `.github/workflows/digest.yml` | GitHub Actions cron job definition |
