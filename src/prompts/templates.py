"""Cached loader for the repository's single YAML prompt catalog."""

from functools import lru_cache
from pathlib import Path

import yaml


@lru_cache(maxsize=1)
def _prompt_catalog() -> dict[str, str]:
    path = Path(__file__).with_name("prompt.yaml")
    prompts = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(prompts, dict) or not all(isinstance(value, str) for value in prompts.values()):
        raise ValueError(f"Invalid prompt catalog: {path}")
    return prompts


def get_prompt_template(prompt_name: str) -> str:
    """Return one named prompt from ``src/prompts/prompt.yaml``."""
    try:
        return _prompt_catalog()[prompt_name]
    except KeyError as exc:
        raise ValueError(f"Unknown prompt template: {prompt_name}") from exc
