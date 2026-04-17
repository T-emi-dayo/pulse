from datetime import datetime, timezone

from src.schemas.state import AgentState, SummaryItem

_SOURCE_ORDER = ["research_paper", "github_release", "docs", "news", "blog"]

_SOURCE_LABELS = {
    "research_paper": "Research Papers",
    "github_release": "GitHub Releases",
    "docs":           "Documentation Updates",
    "news":           "News",
    "blog":           "Blog Posts",
}


class MergeDigestNode:
    """Assembles all summaries into the final digest. No LLM call."""

    def run(self, state: AgentState) -> dict:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        total = len(state.deduped_items)

        by_source: dict[str, SummaryItem] = {s.source_type: s for s in state.summaries}

        lines: list[str] = [
            f"# ⚡ Pulse Daily Digest — {date_str}",
            "",
            f"{total} item{'s' if total != 1 else ''} across "
            f"{len(by_source)} source type{'s' if len(by_source) != 1 else ''}",
            "",
        ]

        for source_type in _SOURCE_ORDER:
            summary = by_source.get(source_type)
            if not summary:
                continue

            label = _SOURCE_LABELS.get(source_type, source_type)
            lines.append(f"## {label}  ({summary.item_count} items)")
            lines.append("")
            lines.append(summary.summary_text.strip())
            lines.append("")

        if state.errors:
            lines.append("---")
            lines.append(f"Errors ({len(state.errors)})")
            lines.append("")
            for err in state.errors:
                lines.append(f"- {err}")

        return {"final_digest": "\n".join(lines)}
