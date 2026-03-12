"""
LLM Article Summarizer
Uses Claude (Anthropic) to generate substantive, professional summaries
of articles for banking and fintech practitioners.
Falls back to the raw text if the API is unavailable or not configured.
"""

import anthropic
from config import ANTHROPIC_API_KEY, ENABLE_SUMMARIZATION

_client = None   # lazy-initialised


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def summarize_article(title: str, raw_text: str) -> str:
    """
    Generate a substantive summary of a single article using Claude Haiku.

    The summary captures what was announced, key numbers/companies, and significance —
    at an appropriate length for the content (not artificially capped).

    Returns raw_text as-is if summarization is disabled or the API call fails.
    """
    if not ENABLE_SUMMARIZATION or not ANTHROPIC_API_KEY:
        return raw_text

    if not raw_text or len(raw_text.strip()) < 40:
        return raw_text

    try:
        client = _get_client()
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=350,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are summarising news for professionals working at consumer banks.\n\n"
                        f"Article title: {title}\n"
                        f"Article text: {raw_text}\n\n"
                        "Write a crisp bullet-point summary. Rules:\n"
                        "• Each bullet must be a standalone fact — no padding, no waffle\n"
                        "• Include specific numbers, company names, product names where present\n"
                        "• The last bullet must state why this matters for a consumer bank\n"
                        "• Use 3-5 bullets total; never more\n"
                        "• Start each bullet with '• ' (bullet + space)\n"
                        "• No intro sentence, no section headers — bullets only\n\n"
                        "Summary:"
                    ),
                }
            ],
        )
        return message.content[0].text.strip()
    except Exception:
        # Never let summarisation failure block the digest
        return raw_text


def summarize_articles(articles: list[dict], verbose: bool = True) -> list[dict]:
    """
    Run summarise_article() over a list of article dicts in place,
    replacing the 'summary' field with the LLM-generated version.

    Skips summarisation if the API key is missing or the feature is disabled,
    and prints a clear message so the user knows why.
    """
    if not ENABLE_SUMMARIZATION:
        return articles

    if not ANTHROPIC_API_KEY:
        if verbose:
            print("  ℹ️  ANTHROPIC_API_KEY not set — using raw RSS summaries")
            print("      Add your key to ANTHROPIC_API_KEY in config.py")
        return articles

    if verbose:
        print(f"\n✍️  Summarising {len(articles)} articles with Claude...")

    for i, article in enumerate(articles, 1):
        original  = article.get("summary", "")
        improved  = summarize_article(article["title"], original)
        article["summary"] = improved

        if verbose and i % 5 == 0:
            print(f"   {i}/{len(articles)} done...")

    if verbose:
        print(f"   Summarisation complete.")

    return articles
