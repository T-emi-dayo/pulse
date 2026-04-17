from typing import Optional, Annotated
import operator
from pydantic import BaseModel, Field
from src.schemas.topic_profile import TopicProfile


class IngestedItem(BaseModel):
    title: str
    url: str
    source_type: str          # "news" | "blog" | "github_release" | "research_paper" | "docs"
    source_name: str          # e.g. "TechCrunch", "langchain-ai/langgraph"
    source_rank: Optional[int] = None  # populated for news/blog only
    topic: str                # which topic profile this came from
    excerpt: str
    published_at: str         # ISO 8601, UTC


class SummaryItem(BaseModel):
    source_type: str
    summary_text: str
    item_count: int


class AgentState(BaseModel):
    # Input
    topic_profiles: list[TopicProfile]

    # Ingestion — operator.add accumulates across parallel nodes
    raw_items: Annotated[list[IngestedItem], operator.add] = Field(default_factory=list)
    deduped_items: list[IngestedItem] = Field(default_factory=list)

    # Summarization — operator.add accumulates across parallel nodes
    summaries: Annotated[list[SummaryItem], operator.add] = Field(default_factory=list)
    final_digest: str = ""

    # Non-fatal errors from any node
    errors: Annotated[list[str], operator.add] = Field(default_factory=list)
