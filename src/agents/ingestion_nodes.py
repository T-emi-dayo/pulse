from datetime import datetime, timezone, timedelta

from src.schemas.state import AgentState, IngestedItem
from src.config.settings import TOP_N_BY_SOURCE, LOOKBACK_HOURS
from src.tools.github_search_tool import fetch_github
from src.tools.doc_search_tool import fetch_docs
from src.tools.research_search_tool import fetch_research_papers
from src.tools.news_tool import fetch_news
from src.tools.blog_tool import fetch_blogs
from src.agents.base_node import BaseNode


def _cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)


def _extract_profiles(state: AgentState, source_type: str) -> dict[str, dict]:
    """Returns {topic: source_config} for all profiles matching source_type."""
    result = {}
    for profile in state.topic_profiles:
        for source in profile["sources"]:
            if source["source_type"] == source_type:
                result[profile["topic"]] = source
    return result


class IngestionNode(BaseNode):

    def get_capabilities(self) -> list[str]:
        return ["ingest_github_releases", "ingest_docs", "ingest_research_papers",
                "ingest_news", "ingest_blogs"]

    def ingest_github_releases(self, state: AgentState) -> dict:
        profiles = _extract_profiles(state, "github_release")
        items: list[IngestedItem] = []
        errors: list[str] = []
        cap = TOP_N_BY_SOURCE["github_release"]
        cutoff = _cutoff()

        for topic, source in profiles.items():
            try:
                raw = fetch_github(source.get("repos", []))
                filtered = [r for r in raw if datetime.fromisoformat(r["published_at"]) >= cutoff]
                for r in filtered[:cap]:
                    repo = r["url"].split("github.com/")[-1].split("/")[0] if "github.com" in r["url"] else ""
                    items.append(IngestedItem(
                        title=r["title"],
                        url=r["url"],
                        source_type=r["source_type"],
                        source_name=repo,
                        source_rank=None,
                        topic=topic,
                        excerpt=r["excerpt"],
                        published_at=r["published_at"],
                    ))
            except Exception as e:
                errors.append(f"[ingest_github] {e}")

        return {"raw_items": items, "errors": errors}

    def ingest_docs(self, state: AgentState) -> dict:
        profiles = _extract_profiles(state, "docs")
        items: list[IngestedItem] = []
        errors: list[str] = []
        cap = TOP_N_BY_SOURCE["docs"]

        for topic, source in profiles.items():
            try:
                raw = fetch_docs(source.get("urls", []))
                for r in raw[:cap]:
                    domain = r["url"].split("/")[2] if r["url"].startswith("http") else ""
                    items.append(IngestedItem(
                        title=r["title"],
                        url=r["url"],
                        source_type="docs",
                        source_name=domain,
                        source_rank=None,
                        topic=topic,
                        excerpt=r["excerpt"],
                        published_at=r["published_at"],
                    ))
            except Exception as e:
                errors.append(f"[ingest_docs] {e}")

        return {"raw_items": items, "errors": errors}

    def ingest_research_papers(self, state: AgentState) -> dict:
        profiles = _extract_profiles(state, "research_paper")
        items: list[IngestedItem] = []
        errors: list[str] = []
        cap = TOP_N_BY_SOURCE["research_paper"]

        for topic, source in profiles.items():
            try:
                search_terms = source.get("keywords", []) + source.get("watchlist", [])
                raw = fetch_research_papers(search_terms, max_results=cap * 2)
                for r in raw[:cap]:
                    source_name = "arxiv" if "arxiv.org" in r["url"] else "huggingface"
                    items.append(IngestedItem(
                        title=r["title"],
                        url=r["url"],
                        source_type="research_paper",
                        source_name=source_name,
                        source_rank=None,
                        topic=topic,
                        excerpt=r["excerpt"],
                        published_at=r["published_at"],
                    ))
            except Exception as e:
                errors.append(f"[ingest_research] {e}")

        return {"raw_items": items, "errors": errors}

    def ingest_news(self, state: AgentState) -> dict:
        profiles = _extract_profiles(state, "news")
        items: list[IngestedItem] = []
        errors: list[str] = []
        cap = TOP_N_BY_SOURCE["news"]

        for topic, source in profiles.items():
            try:
                keywords = source.get("keywords", [])
                if not keywords:
                    continue
                # Join keywords into a single OR query; tool caps results at 5
                query = " OR ".join(keywords)
                raw = fetch_news(query, max_results=cap)
                for rank, r in enumerate(raw, start=1):
                    items.append(IngestedItem(
                        title=r["title"],
                        url=r["url"],
                        source_type="news",
                        source_name=r.get("source") or "ddgs",
                        source_rank=rank,
                        topic=topic,
                        excerpt=r.get("excerpt") or "",
                        published_at=r["published_at"],
                    ))
            except Exception as e:
                errors.append(f"[ingest_news] {e}")

        return {"raw_items": items, "errors": errors}

    def ingest_blogs(self, state: AgentState) -> dict:
        profiles = _extract_profiles(state, "blog")
        items: list[IngestedItem] = []
        errors: list[str] = []
        cap = TOP_N_BY_SOURCE["blog"]

        for topic, source in profiles.items():
            try:
                raw = fetch_blogs(source.get("urls", []), source.get("keywords", []))
                for rank, r in enumerate(raw[:cap], start=1):
                    domain = r["url"].split("/")[2] if r["url"].startswith("http") else ""
                    items.append(IngestedItem(
                        title=r["title"],
                        url=r["url"],
                        source_type="blog",
                        source_name=domain,
                        source_rank=rank,
                        topic=topic,
                        excerpt=r["excerpt"],
                        published_at=r["published_at"],
                    ))
            except Exception as e:
                errors.append(f"[ingest_blogs] {e}")

        return {"raw_items": items, "errors": errors}
