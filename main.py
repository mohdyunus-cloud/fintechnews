"""
AI × Fintech × Retail Intelligence Digest
==========================================
Main entry point. Run this script to fetch news and send the daily digest.

Usage:
    python main.py              → fetch news, summarise, and send email
    python main.py --preview    → generate HTML file without sending email
    python main.py --test       → test with sample articles (no network, no API)
    python main.py --validate   → check all RSS feeds are reachable and report status
"""

import sys
import os
from datetime import datetime, timezone
from config import MAX_ARTICLES_IN_DIGEST, REQUIRE_AI_AND_BANKING


def run(preview_only: bool = False, test_mode: bool = False):
    print("\n" + "═" * 58)
    print("  🤖  AI × Fintech × Retail Intelligence Digest")
    print(f"  {datetime.now(timezone.utc).strftime('%A, %d %B %Y — %H:%M UTC')}")
    print("═" * 58)

    # ── 1. Fetch RSS articles ─────────────────────────────────────────────────
    if test_mode:
        print("\n[TEST MODE] Using sample articles — no network or API calls.")
        primary   = _sample_articles()
        secondary = []
        seen_urls = set()
    else:
        print("\n📡 Fetching news from RSS feeds...")
        from fetcher import fetch_all_feeds
        primary, secondary, seen_urls = fetch_all_feeds(verbose=True)

    # ── 2. Fetch web search articles (Perplexity) ─────────────────────────────
    if not test_mode:
        from web_searcher import fetch_web_search_articles
        from fetcher import score_article

        web_articles = fetch_web_search_articles(seen_rss_urls=seen_urls, verbose=True)

        # Score web search articles and split into primary / secondary
        for art in web_articles:
            art["scores"] = score_article(art["title"], art.get("summary", ""))

        for art in web_articles:
            s = art["scores"]
            is_primary = (
                s["ai"] >= 1 and (s["fintech"] >= 1 or s["retail"] >= 1)
            ) if REQUIRE_AI_AND_BANKING else (s["total"] >= 1)

            if is_primary:
                primary.append(art)
            elif s["total"] >= 1:
                secondary.append(art)

        # Re-sort and cap
        primary.sort(key=lambda a: (a["scores"]["total"], a["date"]), reverse=True)
        primary   = primary[:MAX_ARTICLES_IN_DIGEST]
        secondary = secondary[:30]   # cap secondary at 30 links

    if not primary and not secondary:
        print("\n⚠️  No articles matched your filters today.")
        print("   Try lowering MIN_RELEVANCE_SCORE in config.py, or increasing LOOKBACK_HOURS.")
        return

    # ── 3. Summarise primary articles with Claude (secondary: no LLM) ─────────
    if not test_mode and primary:
        from summarizer import summarize_articles
        primary = summarize_articles(primary, verbose=True)

    # ── 4. Build digest ───────────────────────────────────────────────────────
    print("\n📝 Building digest...")
    from digest_builder import build_digest_html, build_digest_text
    html_body = build_digest_html(primary, secondary)
    text_body = build_digest_text(primary, secondary)

    # ── 5. Save HTML preview ──────────────────────────────────────────────────
    preview_path = os.path.join(os.path.dirname(__file__), "digest_preview.html")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html_body)
    print(f"   HTML preview saved → {preview_path}")

    # ── 6. Send email (unless preview-only) ───────────────────────────────────
    if preview_only:
        print("\n🔍 Preview mode — email NOT sent.")
        print("   Open the preview file in your browser to review the digest.")
    else:
        print("\n📧 Sending email digest...")
        from email_sender import send_digest
        send_digest(html_body, text_body)

    # ── 7. Summary ────────────────────────────────────────────────────────────
    web_count = sum(1 for a in primary + secondary if a.get("web_search"))
    print(f"""
📊 Digest breakdown:
   Primary (AI × Banking) : {len(primary)}
   Secondary (other)      : {len(secondary)}
   🔍 Via web search      : {web_count}
""")


def validate():
    """Run feed validation and print a status report."""
    print("\n" + "═" * 58)
    print("  🔍  RSS Feed Validation Report")
    print(f"  {datetime.now(timezone.utc).strftime('%A, %d %B %Y — %H:%M UTC')}")
    print("═" * 58)
    from fetcher import validate_feeds
    validate_feeds(verbose=True)


def _sample_articles():
    """Generate sample primary articles for testing (no network or API required)."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    return [
        {
            "title":   "Banks Race to Deploy AI Agents for Customer Service",
            "summary": "Major banks including JPMorgan and HSBC are rolling out large language model-powered AI agents to handle customer queries, reducing costs and improving response times in their digital banking apps.",
            "link":    "https://example.com/banks-ai-agents",
            "source":  "Finextra",
            "date":    now - timedelta(hours=3),
            "scores":  {"total": 6, "ai": 3, "fintech": 3, "retail": 0,
                        "tags": ["🤖 AI", "💳 Fintech"], "keywords": ["ai agent", "llm", "banking"]},
        },
        {
            "title":   "AI-Powered Mortgage Underwriting Cuts Approval Times by 60%",
            "summary": "Several high street banks are deploying machine learning models to automate mortgage underwriting, reducing approval times from weeks to days while improving accuracy of affordability assessments.",
            "link":    "https://example.com/ai-mortgage-underwriting",
            "source":  "The Financial Brand",
            "date":    now - timedelta(hours=6),
            "scores":  {"total": 5, "ai": 3, "fintech": 0, "retail": 2,
                        "tags": ["🤖 AI", "🏦 Retail Banking"], "keywords": ["machine learning", "mortgage", "consumer banking"]},
        },
        {
            "title":   "Fraud Detection AI Cuts False Positives by 40%",
            "summary": "A new machine learning fraud detection model deployed by several European neobanks is dramatically reducing false positive rates, improving customer experience while catching more genuine fraud.",
            "link":    "https://example.com/fraud-ai-neobanks",
            "source":  "Fintech Futures",
            "date":    now - timedelta(hours=9),
            "scores":  {"total": 5, "ai": 3, "fintech": 2, "retail": 0,
                        "tags": ["🤖 AI", "💳 Fintech"], "keywords": ["machine learning", "fraud detection", "digital bank"]},
        },
    ]


if __name__ == "__main__":
    if "--validate" in sys.argv:
        validate()
    else:
        preview = "--preview" in sys.argv
        test    = "--test"    in sys.argv
        run(preview_only=preview, test_mode=test)
