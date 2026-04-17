import feedparser
from datetime import datetime, timezone, timedelta

from src.types import RawItem

# Fallback feeds used when a topic profile provides no blog URLs.
# Primary source is always topic_profile.sources[].urls.
DEFAULT_FEEDS: list[str] = [
    "https://huggingface.co/blog/feed.xml",
    "https://blog.langchain.dev/rss/",
    "https://thegradient.pub/rss/",
    "https://towardsdatascience.com/feed",
    "https://lilianweng.github.io/index.xml",
]

CUTOFF_HOURS = 24


def _get_cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=CUTOFF_HOURS)


def _parse_entry_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue
    return None


def fetch_blogs(feed_urls: list[str], keywords: list[str]) -> list[RawItem]:
    """
    Parses RSS feeds and returns posts from the last 24h matching any keyword.

    Args:
        feed_urls: RSS feed URLs from the topic profile. Falls back to DEFAULT_FEEDS
                   if empty.
        keywords: Filter terms; a post is included if any keyword appears in its
                  title or summary (case-insensitive).

    Returns:
        List of RawItem dicts.
    """
    cutoff = _get_cutoff()
    feeds_to_parse = feed_urls if feed_urls else DEFAULT_FEEDS
    items: list[RawItem] = []

    for feed_url in feeds_to_parse:
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            print(f"[blog] Failed to parse feed {feed_url}: {feed.bozo_exception}")
            continue

        for entry in feed.entries:
            published = _parse_entry_date(entry)
            if published is None or published < cutoff:
                continue

            text = f"{entry.title} {entry.get('summary', '')}".lower()
            if keywords and not any(kw.lower() in text for kw in keywords):
                continue

            items.append(
                RawItem(
                    title=entry.title.strip(),
                    url=entry.link,
                    source_type="blog",
                    excerpt=entry.get("summary", "")[:500],
                    published_at=published.isoformat(),
                    content_hash=None,
                    full_content=None,
                )
            )

    return items
