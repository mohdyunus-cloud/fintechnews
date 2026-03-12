"""
RSS Feed Fetcher & Relevance Scorer
Fetches articles from configured RSS feeds, scores them for relevance,
and deduplicates by URL.
"""

import feedparser
import requests
import time
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, urlunparse
from config import (
    RSS_FEEDS, AI_KEYWORDS, FINTECH_KEYWORDS, RETAIL_BANKING_KEYWORDS,
    MAX_ARTICLES_PER_FEED, LOOKBACK_HOURS, MIN_RELEVANCE_SCORE,
    REQUIRE_AI_AND_BANKING,
)

# Mimic a real browser so RSS servers don't block the request
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def _fetch_feed(url: str):
    """
    Fetch an RSS feed using requests (with browser headers) then parse with feedparser.
    Falls back to direct feedparser.parse() if requests fails.
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        return feedparser.parse(resp.content), None
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP {e.response.status_code}"
    except requests.exceptions.ConnectionError:
        return None, "Connection error"
    except requests.exceptions.Timeout:
        return None, "Timed out"
    except Exception as e:
        # Last resort: try feedparser directly
        try:
            return feedparser.parse(url), None
        except Exception:
            return None, str(e)[:40]


def clean_text(text: str) -> str:
    """Strip HTML tags and normalise whitespace."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_url(url: str) -> str:
    """
    Normalise a URL for deduplication: lowercase, strip query params and fragment,
    strip trailing slash.
    """
    try:
        parsed = urlparse(url.lower())
        # Keep scheme + netloc + path only
        clean = urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))
        return clean
    except Exception:
        return url.lower().split("?")[0].rstrip("/")


def score_article(title: str, summary: str) -> dict:
    """
    Score an article for relevance across AI, Fintech, and Retail topics.
    Returns scores and matched keywords for each category.
    """
    combined = (title + " " + summary).lower()

    def match(keywords):
        matched = [kw for kw in keywords if kw in combined]
        return len(matched), matched

    ai_score,      ai_matched      = match(AI_KEYWORDS)
    fintech_score, fintech_matched = match(FINTECH_KEYWORDS)
    retail_score,  retail_matched  = match(RETAIL_BANKING_KEYWORDS)
    total_score = ai_score + fintech_score + retail_score

    return {
        "total":    total_score,
        "ai":       ai_score,
        "fintech":  fintech_score,
        "retail":   retail_score,
        "tags":     _build_tags(ai_score, fintech_score, retail_score),
        "keywords": list(set(ai_matched[:3] + fintech_matched[:3] + retail_matched[:3]))
    }


def _build_tags(ai, fintech, retail) -> list[str]:
    tags = []
    if ai      > 0: tags.append("🤖 AI")
    if fintech > 0: tags.append("💳 Fintech")
    if retail  > 0: tags.append("🏦 Retail Banking")
    return tags


def parse_date(entry) -> datetime:
    """Try to extract a publish date from an RSS entry."""
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)  # fallback: treat as fresh


def validate_feeds(verbose: bool = True) -> dict:
    """
    Test each configured RSS feed and report its status.
    Returns a dict mapping feed label → status string.
    Run via: python main.py --validate
    """
    results = {}
    print("\n  Validating RSS feeds...")
    print(f"\n  {'Source':<35} {'Entries':>8}  Status")
    print("  " + "─" * 62)

    for feed_cfg in RSS_FEEDS:
        url   = feed_cfg["url"]
        label = feed_cfg["label"]

        feed, error = _fetch_feed(url)

        if feed is None:
            status = f"❌  {error}"
            entry_count = "—"
        else:
            n = len(feed.entries)
            if n == 0:
                status = "⚠️   empty feed"
                entry_count = "0"
            else:
                status = "✅"
                entry_count = str(n)

        results[label] = status
        print(f"  {label:<35} {entry_count:>8}  {status}")
        time.sleep(0.3)

    print("  " + "─" * 62)
    ok    = sum(1 for s in results.values() if "✅" in s)
    warn  = sum(1 for s in results.values() if "⚠️" in s)
    fail  = sum(1 for s in results.values() if "❌" in s)
    print(f"  {ok} working  |  {warn} empty  |  {fail} broken\n")
    return results


def fetch_all_feeds(verbose: bool = True):
    """
    Fetch all RSS feeds, filter by recency and relevance, deduplicate by URL.

    Returns:
        primary   - articles at the AI × banking/fintech intersection (get LLM summaries)
        secondary - articles with any relevance but outside the strict intersection
                    (shown as-is, no LLM summarization)
        seen_urls - normalised URL set for deduplication by callers
    """
    cutoff     = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    primary    = []
    secondary  = []
    seen_urls  = set()
    feed_stats = []

    MAX_SECONDARY_PER_FEED = 5   # keep secondary section from bloating

    if verbose:
        print(f"\n  {'Source':<35} {'Pulled':>7} {'Primary':>9} {'Other':>6}  Status")
        print("  " + "─" * 68)

    for feed_cfg in RSS_FEEDS:
        url   = feed_cfg["url"]
        label = feed_cfg["label"]
        pulled    = 0
        n_primary = 0
        n_second  = 0
        status    = "✅"

        feed, error = _fetch_feed(url)

        if feed is None:
            status = f"❌ {error}"
        else:
            total_entries = len(feed.entries)
            skipped_old   = 0

            for entry in feed.entries:
                pub_date = parse_date(entry)
                if pub_date < cutoff:
                    skipped_old += 1
                    continue

                title   = clean_text(getattr(entry, "title",   ""))
                summary = clean_text(getattr(entry, "summary", ""))
                link    = getattr(entry, "link", "#")

                if not title:
                    continue

                # URL deduplication
                url_key = normalize_url(link)
                if url_key in seen_urls:
                    continue
                seen_urls.add(url_key)

                pulled += 1
                scores = score_article(title, summary)

                # Primary: AI + banking/fintech intersection
                is_primary = (
                    scores["total"] >= MIN_RELEVANCE_SCORE and
                    scores["ai"] >= 1 and
                    (scores["fintech"] >= 1 or scores["retail"] >= 1)
                ) if REQUIRE_AI_AND_BANKING else (scores["total"] >= MIN_RELEVANCE_SCORE)

                # Secondary: any keyword match, not already primary
                is_secondary = not is_primary and scores["total"] >= 1

                art = {
                    "title":   title,
                    "summary": summary,
                    "link":    link,
                    "source":  label,
                    "date":    pub_date,
                    "scores":  scores,
                }

                if is_primary and n_primary < MAX_ARTICLES_PER_FEED:
                    primary.append(art)
                    n_primary += 1
                elif is_secondary and n_second < MAX_SECONDARY_PER_FEED:
                    secondary.append(art)
                    n_second += 1

            if total_entries == 0:
                status = "⚠️  empty feed"
            elif pulled == 0 and skipped_old > 0:
                status = f"⚠️  all {skipped_old} older than {LOOKBACK_HOURS}h"
            elif pulled == 0:
                status = "⚠️  no articles found"

        feed_stats.append((label, pulled, n_primary, n_second, status))

        if verbose:
            if "✅" in status or "⚠️" in status:
                print(f"  {label:<35} {pulled:>7} {n_primary:>9} {n_second:>6}  {status}")
            else:
                print(f"  {label:<35} {'—':>7} {'—':>9} {'—':>6}  {status}")

        time.sleep(0.3)

    if verbose:
        print("  " + "─" * 68)
        print(f"  {'TOTAL':<35} {sum(s[1] for s in feed_stats):>7} "
              f"{sum(s[2] for s in feed_stats):>9} "
              f"{sum(s[3] for s in feed_stats):>6}")

    primary.sort(key=lambda a: (a["scores"]["total"], a["date"]), reverse=True)
    secondary.sort(key=lambda a: a["date"], reverse=True)   # secondary: newest first
    return primary, secondary, seen_urls
