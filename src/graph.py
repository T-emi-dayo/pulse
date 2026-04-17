from langgraph.graph import StateGraph, START, END

from src.schemas.state import AgentState
from src.agents.ingestion_nodes import IngestionNode
from src.agents.dedup_node import DedupNode
from src.agents.summarization_node import SummarizationNode
from src.agents.merge_digest_node import MergeDigestNode

_INGESTION_NODES = [
    ("ingest_github", "ingest_github_releases"),
    ("ingest_docs", "ingest_docs"),
    ("ingest_research", "ingest_research_papers"),
    ("ingest_news", "ingest_news"),
    ("ingest_blogs", "ingest_blogs"),
]

_SUMMARIZATION_NODES = [
    ("summarize_github", "summarize_github_releases"),
    ("summarize_docs", "summarize_docs"),
    ("summarize_research", "summarize_research_papers"),
    ("summarize_news", "summarize_news"),
    ("summarize_blogs", "summarize_blogs"),
]


def build_graph():
    ingestion = IngestionNode()
    dedup = DedupNode()
    summarization = SummarizationNode()
    merge = MergeDigestNode()

    graph = StateGraph(AgentState)

    # Register ingestion nodes
    for node_name, method_name in _INGESTION_NODES:
        graph.add_node(node_name, getattr(ingestion, method_name))

    # Register dedup
    graph.add_node("dedup", dedup.run)

    # Register summarization nodes
    for node_name, method_name in _SUMMARIZATION_NODES:
        graph.add_node(node_name, getattr(summarization, method_name))

    # Register merge
    graph.add_node("merge_digest", merge.run)

    # Edges: START → all ingestion nodes (parallel fan-out)
    for node_name, _ in _INGESTION_NODES:
        graph.add_edge(START, node_name)
        graph.add_edge(node_name, "dedup")  # fan-in to dedup

    # dedup → all summarization nodes (parallel fan-out)
    for node_name, _ in _SUMMARIZATION_NODES:
        graph.add_edge("dedup", node_name)
        graph.add_edge(node_name, "merge_digest")  # fan-in to merge

    graph.add_edge("merge_digest", END)

    return graph.compile()


# Module-level compiled graph — import and invoke directly
pulse_graph = build_graph()
