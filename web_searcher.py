"""
Perplexity Web Search Integration
Runs targeted daily searches to catch AI-in-banking/fintech news
that isn't available in any RSS feed (paywalled, announcement-only, etc.).

URL strategy: Perplexity's sonar-pro model places real source URLs in the
`citations` array of the API response, not in the text body. The text uses
[1][2] inline markers. We ask the model to number stories to match citation
order (Story 1 → citations[0], Story 2 → citations[1], etc.) and pull URLs
exclusively from the citations array — never parsed from text.
"""

import requests
import re
from datetime import datetime, timezone
from config import PERPLEXITY_API_KEY, PERPLEXITY_SEARCH_QUERIES, ENABLE_WEB_SEARCH
from fetcher import normalize_url as fetcher_normalize_url

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"


def _is_valid_url(url: str) -> bool:
    """
    Return True if the URL looks like a real external news source URL.
    Rejects empty values, Perplexity self-links, and malformed strings.
    """
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return False
    if len(url) < 16:          # shortest plausible URL: https://a.bc/x
        return False
    if "perplexity.ai" in url.lower():
        return False
    return True


def _run_search(query: str) -> list[dict]:
    """
    Run a single Perplexity search query and return parsed article dicts.
    Returns an empty list on any failure.
    """
    prompt = (
        f"Find 4-5 recent news stories (last 24-48 hours) about: {query}\n\n"
        "Describe each story in a SEPARATE numbered block using EXACTLY this format:\n\n"
        "Story 1:\n"
        "Title: [headline of the story]\n"
        "Summary: [3-4 sentences — what happened, key companies and numbers involved, "
        "and why it matters for consumer banking or fintech]\n\n"
        "Story 2:\n"
        "Title: [headline]\n"
        "Summary: [summary]\n\n"
        "...and so on up to Story 5.\n\n"
        "IMPORTANT: Story 1 corresponds to your citation [1], Story 2 to [2], etc. "
        "Each numbered story must cite exactly one source in that order. "
        "Only include stories genuinely about AI or machine learning applied to "
        "consumer banking, retail banking, or fintech. "
        "Skip purely promotional press releases with no substance."
    )

    try:
        resp = requests.post(
            PERPLEXITY_URL,
            headers={
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()

        # Validate response structure before indexing
        choices = data.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            print("  ⚠️  Perplexity returned no choices in response")
            return []
        content = choices[0].get("message", {}).get("content", "")
        if not content:
            print("  ⚠️  Perplexity returned empty content")
            return []

        citations = data.get("citations", [])
        return _parse_stories(content, citations)

    except requests.exceptions.HTTPError as e:
        print(f"  ⚠️  Perplexity HTTP error: {e.response.status_code}")
        return []
    except requests.exceptions.Timeout:
        print("  ⚠️  Perplexity search timed out")
        return []
    except Exception as e:
        print(f"  ⚠️  Perplexity search failed: {e}")
        return []


def _parse_stories(content: str, citations: list[str]) -> list[dict]:
    """
    Parse a Perplexity response into article dicts.

    URLs come exclusively from the `citations` array: Story N → citations[N-1].
    Title and summary are extracted from the numbered text blocks.
    """
    articles = []
    now = datetime.now(timezone.utc)

    # Split on "Story N:" markers.
    # re.split with a capturing group gives:
    #   [pre-text, "1", body_1, "2", body_2, ...]
    blocks = re.split(
        r"\n\*{0,2}Story\s+(\d+)\*{0,2}\.?\s*:?\s*\n",
        "\n" + content
    )

    i = 1  # index of first story-number capture group
    while i + 1 < len(blocks):
        story_num_str = blocks[i].strip()
        story_body    = blocks[i + 1]
        i += 2

        try:
            story_num = int(story_num_str)
        except ValueError:
            continue

        # Map Story N → citations[N-1]
        citation_index = story_num - 1
        if citation_index < 0 or citation_index >= len(citations):
            continue   # no citation available for this story

        raw_url = citations[citation_index]
        if not _is_valid_url(raw_url):
            continue

        # Extract title and summary by line-prefix matching
        title         = ""
        summary_parts = []
        in_summary    = False

        for line in story_body.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            title_m   = re.match(r"\*{0,2}Title\*{0,2}\s*:\s*(.+)", stripped, re.IGNORECASE)
            summary_m = re.match(r"\*{0,2}Summary\*{0,2}\s*:\s*(.*)", stripped, re.IGNORECASE)

            if title_m:
                title = title_m.group(1).strip()
                # Strip markdown bold markers (**text** or ** text) from title value
                title = re.sub(r'^\*+\s*', '', title)   # leading ** or *
                title = re.sub(r'\s*\*+$', '', title)   # trailing **
                # Strip inline citation numbers [1], [2], [3] etc. from title
                title = re.sub(r'(\s*\[\d+\])+\s*$', '', title)
                title = title.strip()
                in_summary = False
            elif summary_m:
                text = summary_m.group(1).strip()
                if text:
                    summary_parts.append(text)
                in_summary = True
            elif in_summary and stripped and not stripped.startswith("**"):
                summary_parts.append(stripped)

        summary = " ".join(summary_parts).strip()

        if not title or len(title) < 8:
            continue
        if not summary:
            continue

        articles.append({
            "title":      title,
            "summary":    summary,
            "link":       raw_url.strip(),
            "source":     "🔍 Web Search",
            "date":       now,
            "scores":     None,   # scored by caller
            "web_search": True,
        })

    return articles


def fetch_web_search_articles(seen_rss_urls: set = None, verbose: bool = True) -> list[dict]:
    """
    Run all configured Perplexity searches and return unique articles
    not already seen in the RSS article set.

    Args:
        seen_rss_urls: Normalised URL set from RSS fetching. Matches are skipped.
        verbose:       Print progress to stdout.
    """
    if not ENABLE_WEB_SEARCH:
        return []

    if not PERPLEXITY_API_KEY:
        if verbose:
            print("  ℹ️  PERPLEXITY_API_KEY not set — skipping web search")
            print("      Add your key to PERPLEXITY_API_KEY in config.py")
        return []

    if seen_rss_urls is None:
        seen_rss_urls = set()

    if verbose:
        print(f"\n🔍 Running {len(PERPLEXITY_SEARCH_QUERIES)} Perplexity web searches...")

    all_articles = []
    seen_urls    = set(seen_rss_urls)   # copy; don't mutate caller's set

    for query in PERPLEXITY_SEARCH_QUERIES:
        if verbose:
            print(f"   → {query[:70]}...")

        results = _run_search(query)
        new = 0

        for article in results:
            url_key = fetcher_normalize_url(article["link"])
            if url_key not in seen_urls:
                seen_urls.add(url_key)
                all_articles.append(article)
                new += 1

        if verbose:
            print(f"     {new} new stories found")

    if verbose:
        print(f"   Total unique web search results: {len(all_articles)}")

    return all_articles
