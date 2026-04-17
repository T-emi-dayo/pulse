from src.schemas.state import AgentState, IngestedItem, SummaryItem
from src.config.settings import settings
from src.prompts.templates import get_prompt_template
from src.agents.base_node import BaseNode


def _format_items(items: list[IngestedItem]) -> str:
    return "\n\n".join(
        f"- {i.title}\n  URL: {i.url}\n  {i.excerpt}"
        for i in items
    )


class SummarizationNode(BaseNode):

    def get_capabilities(self) -> list[str]:
        return ["summarize_github_releases", "summarize_docs", "summarize_research_papers",
                "summarize_news", "summarize_blogs"]

    def _summarize(self, state: AgentState, source_type: str, prompt_key: str) -> dict:
        items = [i for i in state.deduped_items if i.source_type == source_type]
        if not items:
            return {"summaries": []}

        prompt = get_prompt_template(prompt_key).format(items=_format_items(items))

        try:
            summary_text = self.ai_service.generate(
                prompt=prompt,
                model_name=settings.SUMMARIZATION_MODEL,
            )
        except Exception as e:
            return {"summaries": [], "errors": [f"[summarize_{source_type}] {e}"]}

        return {
            "summaries": [SummaryItem(
                source_type=source_type,
                summary_text=summary_text,
                item_count=len(items),
            )],
        }

    def summarize_github_releases(self, state: AgentState) -> dict:
        return self._summarize(state, "github_release", "summarize_github_release")

    def summarize_docs(self, state: AgentState) -> dict:
        return self._summarize(state, "docs", "summarize_docs")

    def summarize_research_papers(self, state: AgentState) -> dict:
        return self._summarize(state, "research_paper", "summarize_research_paper")

    def summarize_news(self, state: AgentState) -> dict:
        return self._summarize(state, "news", "summarize_news")

    def summarize_blogs(self, state: AgentState) -> dict:
        return self._summarize(state, "blog", "summarize_blog")
