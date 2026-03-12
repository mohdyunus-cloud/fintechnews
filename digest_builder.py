"""
HTML Email Digest Builder
Converts scored article lists into a polished HTML email.

Primary section   — AI × banking/fintech intersection, LLM bullet summaries,
                    sorted by relevance score.
Secondary section — everything else with any keyword relevance, shown as a
                    compact link list (title + source + date + snippet),
                    no LLM summarization.
"""

from datetime import datetime, timezone
from config import MAX_ARTICLES_IN_DIGEST


TAG_COLORS = {
    "🤖 AI":              "#4f46e5",
    "💳 Fintech":         "#0891b2",
    "🏦 Retail Banking":  "#059669",
}


def _relevance_label(score: int):
    if score >= 8:  return ("🔥 Must-Read",  "#b91c1c")
    if score >= 5:  return ("⭐ Top Story",   "#92400e")
    return               ("",               "")


def _tag_badge(tag: str) -> str:
    color = TAG_COLORS.get(tag, "#6b7280")
    return (
        f'<span style="background:{color};color:#fff;font-size:11px;'
        f'padding:2px 8px;border-radius:12px;margin-right:4px;'
        f'display:inline-block;font-weight:600;">{tag}</span>'
    )


def _bullet_html(summary: str) -> str:
    """Convert '• bullet' lines to an HTML <ul>. Falls back to <p>."""
    lines   = [l.strip() for l in summary.splitlines() if l.strip()]
    bullets = [l.lstrip("•").lstrip("-").strip() for l in lines
               if l.startswith(("•", "-"))]

    if bullets:
        items = "".join(
            f'<li style="margin-bottom:5px;line-height:1.5;">{b}</li>'
            for b in bullets
        )
        return (
            f'<ul style="margin:0;padding:0 0 0 18px;color:#4b5563;'
            f'font-size:13px;list-style-type:disc;">{items}</ul>'
        )
    return f'<p style="margin:0;font-size:13px;color:#4b5563;line-height:1.5;">{summary}</p>'


# ── Primary article card (full, with bullets) ──────────────────────────────────

def _primary_card(rank: int, article: dict) -> str:
    tags_html        = "".join(_tag_badge(t) for t in article["scores"]["tags"])
    date_str         = article["date"].strftime("%d %b %Y") if article["date"] else ""
    score            = article["scores"]["total"]
    rel_label, rel_color = _relevance_label(score)
    rel_badge        = (
        f'<span style="background:{rel_color};color:#fff;font-size:11px;'
        f'padding:2px 8px;border-radius:12px;margin-right:4px;font-weight:700;">'
        f'{rel_label}</span>'
    ) if rel_label else ""
    web_badge = (
        '<span style="background:#fef3c7;color:#92400e;font-size:11px;'
        'padding:2px 8px;border-radius:12px;margin-right:4px;font-weight:600;">'
        '🔍 Web</span>'
    ) if article.get("web_search") else ""

    return f"""
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;
                padding:16px 20px;margin-bottom:14px;">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;flex-wrap:wrap;">
        <span style="font-size:12px;font-weight:700;color:#9ca3af;min-width:24px;">#{rank}</span>
        {rel_badge}{tags_html}{web_badge}
      </div>
      <a href="{article['link']}" style="text-decoration:none;">
        <h3 style="margin:0 0 10px 0;font-size:15px;font-weight:700;
                   line-height:1.4;color:#111827;">{article['title']}</h3>
      </a>
      {_bullet_html(article['summary'])}
      <div style="margin-top:10px;font-size:12px;color:#9ca3af;">
        <strong style="color:#374151;">{article['source']}</strong>
        &nbsp;·&nbsp;{date_str}
        &nbsp;·&nbsp;
        <a href="{article['link']}" style="color:#4f46e5;text-decoration:none;">
          Read full article →
        </a>
      </div>
    </div>
    """


# ── Secondary article row (compact: title + meta + snippet) ───────────────────

def _secondary_row(article: dict) -> str:
    date_str  = article["date"].strftime("%d %b") if article["date"] else ""
    tags_html = "".join(_tag_badge(t) for t in article["scores"]["tags"])
    # Take first 180 chars of raw summary as the snippet
    snippet   = article.get("summary", "")
    if len(snippet) > 180:
        snippet = snippet[:177] + "…"

    return f"""
    <div style="padding:10px 0;border-bottom:1px solid #f3f4f6;">
      <div style="margin-bottom:3px;">{tags_html}</div>
      <a href="{article['link']}"
         style="font-size:14px;font-weight:600;color:#374151;text-decoration:none;
                line-height:1.4;">
        {article['title']}
      </a>
      <div style="font-size:12px;color:#9ca3af;margin-top:2px;">
        <strong style="color:#6b7280;">{article['source']}</strong>
        &nbsp;·&nbsp;{date_str}
      </div>
      {f'<p style="margin:4px 0 0 0;font-size:12px;color:#6b7280;line-height:1.4;">{snippet}</p>' if snippet else ""}
    </div>
    """


# ── Full digest ────────────────────────────────────────────────────────────────

def build_digest_html(primary: list[dict], secondary: list[dict] = None) -> str:
    """Build the full HTML email."""
    if secondary is None:
        secondary = []
    primary   = primary[:MAX_ARTICLES_IN_DIGEST]
    now       = datetime.now(timezone.utc).strftime("%A, %d %B %Y")

    ai_count      = sum(1 for a in primary if a["scores"]["ai"]      > 0)
    fintech_count = sum(1 for a in primary if a["scores"]["fintech"] > 0)
    retail_count  = sum(1 for a in primary if a["scores"]["retail"]  > 0)
    web_count     = sum(1 for a in primary + secondary if a.get("web_search"))

    source_counts: dict[str, int] = {}
    for a in primary:
        source_counts[a["source"]] = source_counts.get(a["source"], 0) + 1
    top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    source_pills = "".join(
        f'<span style="background:#f3f4f6;color:#374151;padding:3px 10px;'
        f'border-radius:99px;font-size:12px;margin:3px;display:inline-block;">'
        f'{s} ({c})</span>'
        for s, c in top_sources
    )

    primary_cards  = "".join(_primary_card(i + 1, a) for i, a in enumerate(primary))
    secondary_rows = "".join(_secondary_row(a) for a in secondary)

    secondary_section = f"""
    <div style="margin-top:40px;">
      <h2 style="font-size:16px;font-weight:700;color:#374151;
                 border-bottom:2px solid #e5e7eb;padding-bottom:8px;margin-bottom:4px;">
        Also in the News
        <span style="color:#9ca3af;font-weight:400;font-size:13px;"> — {len(secondary)} items</span>
      </h2>
      <p style="font-size:12px;color:#9ca3af;margin:0 0 12px 0;">
        Relevant but outside the AI × banking core focus — links only, no AI summary.
      </p>
      {secondary_rows}
    </div>
    """ if secondary else ""

    web_note = (
        f'<div style="font-size:12px;color:#6b7280;margin-bottom:8px;">'
        f'🔍 {web_count} articles sourced via Perplexity web search</div>'
    ) if web_count else ""

    return f"""
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AI in Banking Digest</title></head>
<body style="margin:0;padding:0;background:#f9fafb;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:680px;margin:0 auto;padding:20px;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#4f46e5 0%,#0891b2 100%);
                border-radius:14px;padding:28px 32px;margin-bottom:24px;color:#fff;">
      <div style="font-size:12px;opacity:0.8;margin-bottom:4px;
                  letter-spacing:1px;text-transform:uppercase;">Intelligence Digest</div>
      <h1 style="margin:0 0 4px 0;font-size:24px;font-weight:800;">
        AI in Banking &amp; Fintech</h1>
      <p style="margin:0;opacity:0.85;font-size:14px;">{now} — sorted by relevance</p>
    </div>

    <!-- Stats -->
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;
                padding:16px 20px;margin-bottom:20px;">
      <div style="display:flex;gap:12px;flex-wrap:wrap;justify-content:space-around;">
        <div style="text-align:center;">
          <div style="font-size:28px;font-weight:800;color:#4f46e5;">{len(primary)}</div>
          <div style="font-size:12px;color:#6b7280;">Top Stories</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:28px;font-weight:800;color:#4f46e5;">{ai_count}</div>
          <div style="font-size:12px;color:#6b7280;">🤖 AI</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:28px;font-weight:800;color:#0891b2;">{fintech_count}</div>
          <div style="font-size:12px;color:#6b7280;">💳 Fintech</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:28px;font-weight:800;color:#059669;">{retail_count}</div>
          <div style="font-size:12px;color:#6b7280;">🏦 Retail</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:28px;font-weight:800;color:#6b7280;">{len(secondary)}</div>
          <div style="font-size:12px;color:#6b7280;">Also in news</div>
        </div>
      </div>
    </div>

    <!-- Top Sources -->
    <div style="margin-bottom:20px;">
      <div style="font-size:12px;color:#9ca3af;margin-bottom:6px;font-weight:600;
                  text-transform:uppercase;letter-spacing:0.5px;">Sources</div>
      {source_pills}
    </div>

    <!-- Legend -->
    <div style="font-size:12px;color:#6b7280;margin-bottom:16px;">
      🔥 Must-Read (score ≥8) &nbsp;·&nbsp; ⭐ Top Story (score ≥5) &nbsp;·&nbsp; #N = relevance rank
    </div>
    {web_note}

    <!-- Primary articles -->
    {primary_cards}

    <!-- Secondary section -->
    {secondary_section}

    <!-- Footer -->
    <div style="text-align:center;padding:20px 0;color:#9ca3af;font-size:12px;
                border-top:1px solid #e5e7eb;margin-top:20px;">
      AI in Banking Intelligence Digest &nbsp;·&nbsp; Generated automatically
    </div>

  </div>
</body>
</html>
"""


def build_digest_text(primary: list[dict], secondary: list[dict] = None) -> str:
    """Plain-text fallback."""
    if secondary is None:
        secondary = []
    now   = datetime.now(timezone.utc).strftime("%A, %d %B %Y")
    lines = [
        f"AI in Banking & Fintech Digest — {now}",
        "=" * 60,
        "Sorted by relevance (most relevant first)",
        "",
    ]

    for i, a in enumerate(primary[:MAX_ARTICLES_IN_DIGEST], 1):
        tags = " | ".join(a["scores"]["tags"])
        lines += [f"#{i}  {a['title']}", f"    {tags}  |  {a['source']}", f"    {a['link']}"]
        for line in a["summary"].splitlines():
            line = line.strip()
            if line:
                lines.append(f"    {line}")
        lines.append("")

    if secondary:
        lines += ["─" * 60, "ALSO IN THE NEWS", "─" * 60, ""]
        for a in secondary:
            tags = " | ".join(a["scores"]["tags"]) if a["scores"]["tags"] else "General"
            lines += [
                f"  {a['title']}",
                f"  {tags}  |  {a['source']}  |  {a['link']}",
                "",
            ]

    return "\n".join(lines)
