"""
Topic profiles for Pulse — curated for an AI/ML Engineer.

Priority scale: 1 = highest signal, 3 = lowest.
Each source type is optional per-topic; omit the key if not relevant.
"""

from src.schemas.topic_profile import TopicProfile

TOPIC_PROFILES: list[TopicProfile] = [
    # ── 1. LLM Agents & Frameworks ──────────────────────────────────────────────
    {
        "topic": "LLM Agents & Frameworks",
        "priority": 1,
        "sources": [
            {
                "source_type": "github_release",
                "keywords": [],
                "urls": [],
                "repos": [
                    "langchain-ai/langchain",
                    "langchain-ai/langgraph",
                    "run-llama/llama_index",
                    "microsoft/autogen",
                    "crewAIInc/crewAI",
                    "pydantic/pydantic-ai",
                    "BerriAI/litellm",
                ],
                "watchlist": [],
            },
            {
                "source_type": "research_paper",
                "keywords": [
                    "LLM agent", "AI agent", "tool use", "function calling",
                    "multi-agent", "ReAct", "agentic", "chain-of-thought",
                    "planning LLM",
                ],
                "urls": [],
                "repos": [],
                "watchlist": ["cs.AI", "cs.CL"],
            },
            {
                "source_type": "news",
                "keywords": [
                    "LangChain", "LlamaIndex", "AI agent", "agentic AI",
                    "autonomous agent", "LLM framework", "AutoGen",
                ],
                "urls": [],
                "repos": [],
                "watchlist": [],
            },
            {
                "source_type": "blog",
                "keywords": [
                    "agent", "LangGraph", "LangChain", "LlamaIndex",
                    "tool use", "multi-agent",
                ],
                "urls": [],   # falls back to DEFAULT_FEEDS in blog_tool.py
                "repos": [],
                "watchlist": [],
            },
        ],
    },

    # ── 2. Foundation Models & Research ─────────────────────────────────────────
    {
        "topic": "Foundation Models & Research",
        "priority": 1,
        "sources": [
            {
                "source_type": "github_release",
                "keywords": [],
                "urls": [],
                "repos": [
                    "openai/openai-python",
                    "anthropics/anthropic-sdk-python",
                    "google-gemini/generative-ai-python",
                    "mistralai/mistral-inference",
                    "meta-llama/llama-stack",
                ],
                "watchlist": [],
            },
            {
                "source_type": "docs",
                "keywords": [],
                "urls": [
                    "https://platform.openai.com/docs/overview",
                    "https://docs.anthropic.com/en/docs/welcome",
                    "https://ai.google.dev/gemini-api/docs",
                ],
                "repos": [],
                "watchlist": [],
            },
            {
                "source_type": "research_paper",
                "keywords": [
                    "large language model", "transformer", "pretraining",
                    "instruction tuning", "RLHF", "DPO", "scaling law",
                    "multimodal", "vision language model",
                ],
                "urls": [],
                "repos": [],
                "watchlist": ["cs.LG", "cs.CL", "cs.AI"],
            },
            {
                "source_type": "news",
                "keywords": [
                    "GPT", "Claude", "Gemini", "Llama", "Mistral",
                    "foundation model", "large language model", "frontier model",
                    "AI model release",
                ],
                "urls": [],
                "repos": [],
                "watchlist": [],
            },
        ],
    },

    # ── 3. MLOps & AI Infrastructure ────────────────────────────────────────────
    {
        "topic": "MLOps & AI Infrastructure",
        "priority": 2,
        "sources": [
            {
                "source_type": "github_release",
                "keywords": [],
                "urls": [],
                "repos": [
                    "vllm-project/vllm",
                    "ggerganov/llama.cpp",
                    "ollama/ollama",
                    "mlflow/mlflow",
                    "ray-project/ray",
                    "huggingface/transformers",
                    "chroma-core/chroma",
                    "qdrant/qdrant",
                ],
                "watchlist": [],
            },
            {
                "source_type": "docs",
                "keywords": [],
                "urls": [
                    "https://huggingface.co/docs/transformers/index",
                    "https://docs.ray.io/en/latest/index.html",
                ],
                "repos": [],
                "watchlist": [],
            },
            {
                "source_type": "research_paper",
                "keywords": [
                    "model serving", "inference optimization", "quantization",
                    "LLM deployment", "speculative decoding", "KV cache",
                    "vector database", "RAG", "retrieval augmented",
                ],
                "urls": [],
                "repos": [],
                "watchlist": ["cs.LG", "cs.DC"],
            },
            {
                "source_type": "news",
                "keywords": [
                    "MLOps", "model serving", "vector database", "AI infrastructure",
                    "GPU cloud", "inference API", "model deployment",
                ],
                "urls": [],
                "repos": [],
                "watchlist": [],
            },
        ],
    },

    # ── 4. Open Source Models & Fine-tuning ─────────────────────────────────────
    {
        "topic": "Open Source Models & Fine-tuning",
        "priority": 2,
        "sources": [
            {
                "source_type": "github_release",
                "keywords": [],
                "urls": [],
                "repos": [
                    "unslothai/unsloth",
                    "huggingface/trl",
                    "huggingface/peft",
                    "microsoft/LoRA",
                    "pytorch/torchtune",
                ],
                "watchlist": [],
            },
            {
                "source_type": "research_paper",
                "keywords": [
                    "fine-tuning", "LoRA", "QLoRA", "PEFT", "open source LLM",
                    "open weights", "SFT", "supervised fine-tuning",
                    "model alignment", "preference optimization",
                ],
                "urls": [],
                "repos": [],
                "watchlist": ["cs.LG", "cs.CL"],
            },
            {
                "source_type": "news",
                "keywords": [
                    "open source AI", "open weights", "Hugging Face",
                    "fine-tuning", "model release", "Llama", "Mistral", "Qwen",
                ],
                "urls": [],
                "repos": [],
                "watchlist": [],
            },
            {
                "source_type": "blog",
                "keywords": [
                    "fine-tuning", "LoRA", "open source model", "PEFT",
                    "model training", "alignment",
                ],
                "urls": [],
                "repos": [],
                "watchlist": [],
            },
        ],
    },

    # ── 5. AI Safety & Evaluation ───────────────────────────────────────────────
    {
        "topic": "AI Safety & Evaluation",
        "priority": 3,
        "sources": [
            {
                "source_type": "research_paper",
                "keywords": [
                    "AI safety", "alignment", "red teaming", "jailbreak",
                    "hallucination", "LLM evaluation", "benchmark", "MMLU",
                    "constitutional AI", "robustness",
                ],
                "urls": [],
                "repos": [],
                "watchlist": ["cs.AI", "cs.CL"],
            },
            {
                "source_type": "news",
                "keywords": [
                    "AI safety", "AI regulation", "responsible AI",
                    "AI governance", "AI risk", "model evaluation",
                    "AI benchmark",
                ],
                "urls": [],
                "repos": [],
                "watchlist": [],
            },
        ],
    },
]
