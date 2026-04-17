PROMPTS: dict[str, str] = {
    "summarize_research_paper": (
        "You are a research analyst covering AI and machine learning.\n\n"
        "Research papers published in the last 24 hours across all tracked topics:\n\n"
        "{items}\n\n"
        "Write a single cohesive 4-6 sentence summary that synthesises the most important "
        "findings and contributions across these papers. Highlight recurring themes, "
        "standout results, and what practitioners should pay attention to. "
        "Be direct and technical. No filler phrases."
    ),
    "summarize_github_release": (
        "You are a developer tracking AI/ML tooling releases.\n\n"
        "GitHub releases from the last 24 hours across all tracked repositories:\n\n"
        "{items}\n\n"
        "Write a single cohesive 3-5 sentence summary of the most significant releases. "
        "Call out any breaking changes, standout new features, or patterns across the ecosystem. "
        "Focus on what a practitioner should actually act on."
    ),
    "summarize_docs": (
        "You are tracking documentation changes across AI/ML tools.\n\n"
        "Documentation pages with detected changes from the last 24 hours:\n\n"
        "{items}\n\n"
        "Write a 2-4 sentence summary covering what changed across these docs "
        "and what developers need to know."
    ),
    "summarize_news": (
        "You are an AI industry analyst.\n\n"
        "News articles from the last 24 hours across all tracked topics:\n\n"
        "{items}\n\n"
        "Write a single cohesive 4-6 sentence briefing of the most important developments. "
        "Separate signal from noise. Focus on what actually matters for AI practitioners "
        "and researchers — skip hype."
    ),
    "summarize_blog": (
        "You are tracking the AI/ML engineering and research blogosphere.\n\n"
        "Blog posts from the last 24 hours across all tracked topics:\n\n"
        "{items}\n\n"
        "Write a single cohesive 3-5 sentence summary of the key insights, techniques, "
        "and ideas shared across these posts."
    ),
}


def get_prompt_template(prompt_name: str) -> str:
    if prompt_name not in PROMPTS:
        raise ValueError(f"Unknown prompt template: {prompt_name}")
    return PROMPTS[prompt_name]
