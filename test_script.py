from src.graph import pulse_graph

topic_profiles = [
    {
        "topic": "LLM Frameworks & Orchestration",
        "priority": 1,
        "sources": [
            {
                "source_type": "github_release",
                "keywords": [],
                "urls": [],
                "repos": [
                    "langchain-ai/langgraph",           # ✓ verified — primary framework
                    "langchain-ai/langchain",            # ✓ verified — core lib
                    "langchain-ai/langchain-google",     # ✓ verified — your genai/vertexai integration
                    "anthropics/anthropic-sdk-python",   # ✓ verified — Anthropic official SDK
                    "BerriAI/litellm",                   # ✓ verified — LLM proxy / multi-provider
                ],
                "watchlist": []
            },
            {
                "source_type": "docs",
                "keywords": [],
                "urls": [
                    "https://langchain-ai.github.io/langgraph/",   # ✓ verified
                    "https://python.langchain.com/docs/introduction/",  # ✓ verified
                ],
                "repos": [],
                "watchlist": []
            },
            {
                "source_type": "research_paper",
                "keywords": ["agent", "multi-agent", "LLM orchestration", "tool use"],
                "urls": [],
                "repos": [],
                "watchlist": ["cs.AI", "cs.CL"]   # ✓ verified arXiv categories
            },
            {
                "source_type": "news",
                "keywords": [
                    "LangGraph", "LangChain", "agentic AI", "multi-agent systems",
                    "LLM agents", "agent orchestration"
                ],
                "urls": [],
                "repos": [],
                "watchlist": []
            },
            {
                "source_type": "blog",
                "keywords": [
                    "agent architecture", "LangGraph tutorial",
                    "multi-agent", "ReAct agent", "agentic workflows"
                ],
                "urls": [],
                "repos": [],
                "watchlist": []
            }
        ]
    },
    {
        "topic": "Gemini & Google AI",
        "priority": 2,
        "sources": [
            {
                "source_type": "github_release",
                "keywords": [],
                "urls": [],
                "repos": [
                    "googleapis/python-genai",          # ✓ verified — NEW unified Google GenAI SDK (replaces google-generativeai)
                    "googleapis/python-aiplatform",     # ✓ verified — Vertex AI SDK
                    "langchain-ai/langchain-google",    # ✓ verified — LangChain ↔ Google bridge
                ],
                "watchlist": []
            },
            {
                "source_type": "docs",
                "keywords": [],
                "urls": [
                    "https://ai.google.dev/gemini-api/docs",  # ✓ verified — Gemini API docs
                    "https://googleapis.github.io/python-genai/",  # ✓ verified — python-genai SDK docs
                ],
                "repos": [],
                "watchlist": []
            },
            {
                "source_type": "research_paper",
                "keywords": ["Gemini", "Gemma", "Google DeepMind", "multimodal LLM"],
                "urls": [],
                "repos": [],
                "watchlist": ["cs.CL", "cs.LG"]
            },
            {
                "source_type": "news",
                "keywords": [
                    "Gemini API", "Gemini 2.5", "Google AI Studio",
                    "Vertex AI", "Google DeepMind"
                ],
                "urls": [],
                "repos": [],
                "watchlist": []
            }
        ]
    },
    {
        "topic": "LLM Evaluation & Observability",
        "priority": 3,
        "sources": [
            {
                "source_type": "github_release",
                "keywords": [],
                "urls": [],
                "repos": [
                    "confident-ai/deepeval",            # ✓ verified — your active eval framework
                    "langchain-ai/langsmith-sdk",       # ✓ verified — LangSmith tracing/evals
                ],
                "watchlist": []
            },
            {
                "source_type": "docs",
                "keywords": [],
                "urls": [
                    "https://deepeval.com/docs/getting-started",       # ✓ verified
                    "https://docs.smith.langchain.com/",               # ✓ verified
                ],
                "repos": [],
                "watchlist": []
            },
            {
                "source_type": "research_paper",
                "keywords": [
                    "LLM evaluation", "LLM-as-a-judge", "benchmark",
                    "hallucination detection", "G-Eval", "RAG evaluation"
                ],
                "urls": [],
                "repos": [],
                "watchlist": ["cs.CL", "cs.AI"]
            },
            {
                "source_type": "news",
                "keywords": [
                    "LLM evaluation", "LLMOps", "LLM observability",
                    "model benchmarking", "AI quality"
                ],
                "urls": [],
                "repos": [],
                "watchlist": []
            },
            {
                "source_type": "blog",
                "keywords": [
                    "LLM-as-a-judge", "eval pipeline", "GEval",
                    "prompt regression", "LLM testing"
                ],
                "urls": [],
                "repos": [],
                "watchlist": []
            }
        ]
    },
    {
        "topic": "Foundation Models & Research",
        "priority": 4,
        "sources": [
            {
                "source_type": "research_paper",
                "keywords": [
                    "large language model", "reasoning", "chain-of-thought",
                    "instruction tuning", "RLHF", "RAG", "retrieval augmented generation"
                ],
                "urls": [],
                "repos": [],
                "watchlist": ["cs.LG", "cs.CL", "cs.AI", "stat.ML"]  # ✓ verified arXiv categories
            },
            {
                "source_type": "github_release",
                "keywords": [],
                "urls": [],
                "repos": [
                    "anthropics/anthropic-sdk-python",  # ✓ already tracked above, intentional overlap for model releases
                    "googleapis/python-genai",          # ✓ same
                ],
                "watchlist": []
            },
            {
                "source_type": "news",
                "keywords": [
                    "foundation model", "GPT", "Claude", "Gemini release",
                    "open source LLM", "model release"
                ],
                "urls": [],
                "repos": [],
                "watchlist": []
            }
        ]
    }
]

def main():
    from ddgs import DDGS
    from src.tools.news_tool import fetch_news
    
    results = fetch_news(query="sun or moon or stars", max_results=5)
    print(results)

if __name__ == "__main__":
    main()