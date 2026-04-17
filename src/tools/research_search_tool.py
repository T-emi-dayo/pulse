import arxiv
import feedparser
from datetime import datetime, timezone, timedelta

from src.types import RawItem


HF_RSS_URL = "https://huggingface.co/papers.rss"
CUTOFF_HOURS = 24


def _get_cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=CUTOFF_HOURS)


def fetch_arxiv_papers(keywords: list[str], max_results: int = 20) -> list[RawItem]:
    cutoff = _get_cutoff()
    client = arxiv.Client()
    query = " OR ".join(keywords)

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    items: list[RawItem] = []
    for result in client.results(search):
        if result.published < cutoff:
            break  # results are date-ordered, safe to break early
        items.append(
            RawItem(
                title=result.title.strip(),
                url=result.entry_id,
                source_type="research_paper",
                excerpt=result.summary[:500],
                published_at=result.published.isoformat(),
                content_hash=None,
            )
        )

    return items


def fetch_huggingface_papers(keywords: list[str]) -> list[RawItem]:
    cutoff = _get_cutoff()
    feed = feedparser.parse(HF_RSS_URL)

    items: list[RawItem] = []
    for entry in feed.entries:
        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        if published < cutoff:
            continue

        text = f"{entry.title} {entry.get('summary', '')}".lower()
        if not any(kw.lower() in text for kw in keywords):
            continue

        items.append(
            RawItem(
                title=entry.title.strip(),
                url=entry.link,
                source_type="research_paper",
                excerpt=entry.get("summary", "")[:500],
                published_at=published.isoformat(),
                content_hash=None,
            )
        )

    return items


def fetch_research_papers(keywords: list[str], max_results: int = 20) -> list[RawItem]:
    arxiv_items = fetch_arxiv_papers(keywords, max_results)
    hf_items = fetch_huggingface_papers(keywords)

    seen: set[str] = set()
    combined: list[RawItem] = []
    for item in arxiv_items + hf_items:
        if item["url"] not in seen:
            seen.add(item["url"])
            combined.append(item)

    return combined