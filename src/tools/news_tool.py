from datetime import datetime, timezone, timedelta

from ddgs import DDGS

from src.types import RawItem

CUTOFF_HOURS = 24


def _get_cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=CUTOFF_HOURS)


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None


ddgs = DDGS()
def fetch_news(query, max_results: int = 5) -> list[RawItem]:
    """
    Fetches recent news via DuckDuckGo News search (no API key required).

    Args:
        query: Search query.
        max_results: Max articles to return.

    Returns:
        List of RawItem dicts for articles published within the last 24h.
    """
    if not query:
        return []

    cutoff = _get_cutoff()
    items: list[RawItem] = []

    try:
        results = DDGS().news(
            query=query,
            region="wt-wt",
            safesearch="off",
            timelimit="d",          # last 24 hours
            max_results=max_results,
        )
    except Exception as e:
        print(f"[news] DDGS search failed: {e}")
        return []

    for article in results:
        title = (article.get("title") or "").strip()
        url = (article.get("url") or "").strip()
        body = (article.get("body") or "").strip()
        source = (article.get("source") or "").strip()
        if not title or not url:
            continue

        published = _parse_date(article.get("date", ""))
        if published and published < cutoff:
            continue

        published_at = published.isoformat() if published else datetime.now(timezone.utc).isoformat()

        items.append(
            RawItem(
                title=title,
                url=url,
                source_type="news",
                source= source if source else None,
                excerpt=body if body else None,
                published_at=published_at,
                content_hash=None,
                full_content=None,
            )
        )

    return items
