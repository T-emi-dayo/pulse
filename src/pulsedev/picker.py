"""Prompt construction and structured weekly candidate generation."""

import json

from src.config.settings import settings
from src.prompts.templates import get_prompt_template
from src.pulsedev.schemas import PickProposal
from src.pulsedev.user_profile import LearningEvidence, UserProfile
from src.services.AIService import AIService


def _compact_profile(profile: UserProfile | dict) -> dict:
    model = profile if isinstance(profile, UserProfile) else UserProfile.model_validate(profile)
    return {
        "summary": model.summary[:600],
        "knowledge_notes": model.knowledge_notes[:600],
        "sections": [
            {
                "id": section.id,
                "name": section.name,
                "items": [
                    {"id": item.id, "name": item.name}
                    for item in section.items if item.merged_into is None
                ],
            }
            for section in model.sections
        ],
    }


def _compact_pending_evidence(evidence: list[LearningEvidence | dict] | None) -> list[dict]:
    result = []
    for entry in evidence or []:
        item = entry if isinstance(entry, LearningEvidence) else LearningEvidence.model_validate(entry)
        result.append({
            "pick_id": item.pick_id,
            "title": item.title,
            "status": "done",
        })
    return result


def build_picker_prompt(
    digests: list[dict],
    profile: UserProfile | dict,
    blocked_topics: list[dict] | None = None,
    lower_friction: bool = False,
    pending_evidence: list[LearningEvidence | dict] | None = None,
) -> str:
    """Build a compact picker context; Python retains all profile history and dates."""
    context = {
        "profile": _compact_profile(profile),
        "pending_completed_work": _compact_pending_evidence(pending_evidence),
        "deferred_topics": [
            {key: topic.get(key) for key in ("title", "reason", "avoid_until") if topic.get(key)}
            for topic in blocked_topics or []
        ],
        "weekly_digests": [{"content": digest.get("content", "")} for digest in digests],
    }
    return get_prompt_template("pulsedev_picker").format(
        lower_friction="yes" if lower_friction else "no",
        context_json=json.dumps(context, ensure_ascii=False, separators=(",", ":")),
    )


def choose_pick(prompt: str) -> dict:
    llm = AIService().call_llm(model_name=settings.INGESTION_MODEL)
    response = llm.with_structured_output(PickProposal).invoke(prompt)
    return response.model_dump(mode="json")
