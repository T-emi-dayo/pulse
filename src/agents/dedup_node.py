from src.schemas.state import AgentState, IngestedItem


class DedupNode:
    """Deduplicates raw_items by URL, preserving first-seen order."""

    def run(self, state: AgentState) -> dict:
        seen: set[str] = set()
        deduped: list[IngestedItem] = []

        for item in state.raw_items:
            if item.url not in seen:
                seen.add(item.url)
                deduped.append(item)

        return {"deduped_items": deduped}
