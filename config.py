"""
Configuration for AI Intelligence Digest Tool

Sensitive values (API keys, email credentials) are read from environment
variables so this file can be committed to version control safely.

Local development  → export before running, or use a .env loader:
    export EMAIL_SENDER="you@gmail.com"
    export EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"   # Gmail App Password
    export EMAIL_RECIPIENTS="a@b.com,c@d.com"     # comma-separated
    export PERPLEXITY_API_KEY="pplx-..."
    export ANTHROPIC_API_KEY="sk-ant-..."

GitHub Actions     → store the five names above as repository Secrets;
                     the workflow injects them automatically.
                     See .github/workflows/digest.yml.
"""

import os

# ─────────────────────────────────────────────
# EMAIL SETTINGS  (injected via environment variables)
# ─────────────────────────────────────────────
EMAIL_SENDER    = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD  = os.environ.get("EMAIL_PASSWORD", "")   # Gmail App Password
                                                          # myaccount.google.com → Security → App Passwords
_recipients_raw = os.environ.get("EMAIL_RECIPIENTS", "")
EMAIL_RECIPIENTS = [r.strip() for r in _recipients_raw.split(",") if r.strip()]
EMAIL_SUBJECT   = "🤖 Daily AI × Fintech × Retail Banking Intelligence Digest"

# ─────────────────────────────────────────────
# API KEYS  (injected via environment variables)
# ─────────────────────────────────────────────
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")   # https://www.perplexity.ai/settings/api
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY",  "")   # https://console.anthropic.com/

# ─────────────────────────────────────────────
# DIGEST SETTINGS
# ─────────────────────────────────────────────
MAX_ARTICLES_PER_FEED   = 10    # Max articles to pull per RSS feed
MAX_ARTICLES_IN_DIGEST  = 40    # Max total articles to include in the email
LOOKBACK_HOURS          = 48    # Only include articles from the past N hours
MIN_RELEVANCE_SCORE     = 2     # Minimum keyword match score to include an article

# ─────────────────────────────────────────────
# FEATURE FLAGS
# ─────────────────────────────────────────────
ENABLE_WEB_SEARCH     = True   # Use Perplexity to find stories not in any RSS feed
ENABLE_SUMMARIZATION  = True   # Use Claude to generate substantive article summaries

# Require every article to match at least one AI keyword AND at least one
# banking/fintech keyword. This keeps the digest focused on AI *applied to*
# banking rather than generic tech or generic banking news.
REQUIRE_AI_AND_BANKING = True

# ─────────────────────────────────────────────
# WEB SEARCH QUERIES (Perplexity)
# These run daily to catch paywalled/non-RSS news. Edit freely.
# ─────────────────────────────────────────────
PERPLEXITY_SEARCH_QUERIES = [
    "AI machine learning consumer retail banking product launch announcement last 48 hours",
    "artificial intelligence fraud detection credit scoring digital banking fintech news this week",
    "bank generative AI LLM chatbot customer service mortgage loan underwriting deployment news",
    "AI banking regulation consumer protection CFPB FCA OCC fintech compliance announcement recent",
]

# ─────────────────────────────────────────────
# RSS FEED SOURCES
# ─────────────────────────────────────────────
RSS_FEEDS = [
    # ── AI & Technology ───────────────────────
    {"url": "https://venturebeat.com/category/ai/feed/",                       "label": "VentureBeat AI"},
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/",   "label": "TechCrunch AI"},
    {"url": "https://www.technologyreview.com/feed/",                          "label": "MIT Tech Review"},
    {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml","label": "The Verge AI"},
    {"url": "https://feeds.wired.com/wired/index",                             "label": "Wired"},
    {"url": "https://aibusiness.com/rss.xml",                                  "label": "AI Business"},
    {"url": "https://openai.com/blog/rss.xml",                                 "label": "OpenAI Blog"},
    {"url": "https://huggingface.co/blog/feed.xml",                            "label": "HuggingFace Blog"},

    # ── Fintech Specialist ────────────────────
    {"url": "https://www.finextra.com/rss/headlines.aspx",                     "label": "Finextra"},
    {"url": "https://www.pymnts.com/feed/",                                    "label": "PYMNTS"},
    {"url": "https://news.google.com/rss/search?q=site:fintechfutures.com+fintech+AI&hl=en-US&gl=US&ceid=US:en", "label": "Fintech Futures"},
    {"url": "https://tearsheet.co/feed/",                                      "label": "Tearsheet"},
    {"url": "https://thefintechtimes.com/feed/",                               "label": "The Fintech Times"},
    {"url": "https://finovate.com/feed/",                                      "label": "Finovate"},
    {"url": "https://news.google.com/rss/search?q=site:fintechnexus.com+AI+fintech&hl=en-US&gl=US&ceid=US:en", "label": "Fintech Nexus"},

    # ── Banking & Consumer Finance ────────────
    {"url": "https://news.google.com/rss/search?q=site:thefinancialbrand.com+AI+banking&hl=en-US&gl=US&ceid=US:en", "label": "The Financial Brand"},
    {"url": "https://www.bankingdive.com/feeds/news/",                         "label": "Banking Dive"},
    {"url": "https://news.google.com/rss/search?q=site:americanbanker.com+AI+fintech&hl=en-US&gl=US&ceid=US:en", "label": "American Banker"},
    {"url": "https://www.crowdfundinsider.com/feed/",                          "label": "Crowdfund Insider"},
    {"url": "https://www.consumerfinance.gov/about-us/blog/feed/",             "label": "CFPB Blog"},

    # ── Regulatory ────────────────────────────
    {"url": "https://www.occ.gov/tools-resources/rss-feeds/occ-news.xml",      "label": "OCC (US)"},
    {"url": "https://www.fca.org.uk/news/rss.xml",                             "label": "FCA (UK)"},
]

# ─────────────────────────────────────────────
# RELEVANCE KEYWORDS
# Articles must mention at least MIN_RELEVANCE_SCORE of these to be included
# ─────────────────────────────────────────────
AI_KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning", "neural network",
    "large language model", "llm", "generative ai", "gen ai", "gen-ai", "foundation model",
    "chatgpt", "gpt-4", "gpt-5", "gpt-o1", "claude", "gemini", "mistral", "llama",
    "natural language processing", "nlp", "computer vision", "ai model",
    "ai agent", "agentic ai", "ai assistant", "copilot", "automation",
    "ai-powered", "ai platform", "ai-driven", "ai solution", "ai tool",
    "predictive analytics", "recommendation engine", "anomaly detection",
    "fraud detection", "credit scoring", "risk model", "underwriting ai",
    "vector database", "embedding", "fine-tuning", "rag", "retrieval augmented",
]

FINTECH_KEYWORDS = [
    # Core consumer banking & fintech
    "fintech", "financial technology", "payments", "neobank", "digital bank",
    "challenger bank", "banking", "lending", "credit", "loan",
    # Regulatory & compliance (directly impacts retail banks)
    "regtech", "insurtech",
    # Digital banking channels & products
    "open banking", "embedded finance", "buy now pay later", "bnpl",
    "digital wallet", "mobile payments", "kyc", "aml",
    "compliance", "financial inclusion", "digital lending",
    # Infrastructure affecting consumer banks
    "api banking", "banking as a service", "baas",
    "payment processing", "real-time payments", "instant payments",
    "core banking", "loan origination", "credit risk", "customer experience",
    "financial services",
    # Consumer-facing concepts
    "personal finance", "bank account", "savings",
]

RETAIL_BANKING_KEYWORDS = [
    # Bank types & segments
    "retail banking", "consumer banking", "personal banking", "high street bank",
    # Core products
    "current account", "savings account", "checking account", "deposit",
    "mortgage", "home loan", "personal loan", "overdraft", "credit card",
    "debit card",
    # Channels
    "branch banking", "atm", "digital banking", "online banking", "mobile banking",
    "voice banking", "bank app",
    # AI-specific interaction points in retail banking
    "chatbot", "virtual assistant", "personal finance management", "pfm",
    "financial coach", "next best action", "customer retention",
    # Processes & customer lifecycle
    "customer onboarding", "know your customer", "kyc", "account opening",
    "customer acquisition", "churn", "lifetime value", "net promoter score",
    # Consumer financial health
    "financial wellbeing", "financial inclusion", "underbanked", "unbanked",
    "consumer credit", "affordability", "debt management",
    # Infrastructure & regulation
    "open banking", "psd2", "account aggregation",
    "bank of england", "federal reserve", "fdic", "occ", "prudential regulation",
]
