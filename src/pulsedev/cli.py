"""Interactive local tools for editing the profile and previewing PulseDev picks."""

import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from src.config.settings import settings
from src.pulsedev.digests import digest_date, week_window
from src.pulsedev.learning_repo import _parse_pick
from src.pulsedev.picker import build_picker_prompt, choose_pick
from src.pulsedev.status_policy import preview_weekly_policy
from src.pulsedev.user_profile import (
    UserProfile,
    make_profile_section,
    pending_profile_evidence,
    read_profile,
    section_items,
    sync_completed_evidence,
    write_profile,
)

ROOT = Path(__file__).resolve().parents[2]


def _learning_path(argument: str | None) -> Path:
    value = argument or settings.LEARNING_LOG_PATH
    if not value:
        value = input("Path to your local learning-log checkout (Enter for ./learning-log): ").strip()
    path = Path(value or "learning-log").expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _ask(label: str, default: str) -> str:
    answer = input(f"{label} [{default}]: ").strip()
    return answer or default


def _items(label: str, current: list[str]) -> list[str]:
    answer = input(f"Add {label} (comma-separated, Enter to keep current) [{', '.join(current)}]: ").strip()
    additions = [item.strip() for item in answer.split(",") if item.strip()] if answer else []
    known = {item.casefold() for item in current}
    return current + [item for item in additions if item.casefold() not in known]


def _update_section(profile: UserProfile, name: str, names: list[str]) -> None:
    section = next((item for item in profile.sections if item.name.casefold() == name.casefold()), None)
    if section is None:
        profile.sections.append(make_profile_section(name, names))
        return
    known = {item.name.casefold() for item in section.items}
    for value in names:
        if value.casefold() not in known:
            section.items.extend(make_profile_section(name, [value]).items)
            known.add(value.casefold())


def _profile_init(path: Path, save: bool = True) -> UserProfile:
    profile_path = path / "profile.json"
    existing = read_profile(profile_path) if profile_path.exists() else UserProfile(summary="", evidence=[])
    section_defaults = {
        "Knowledge areas": ["LLM and agentic systems"],
        "Strengths": ["LLM and agentic systems"],
        "Interests": ["Personal tools and useful workflows"],
        "Growth areas": ["Backend", "Deployment", "Mathematics", "Theory"],
        "Learning preferences": ["Weekly scope", "Mix of practical and abstract work"],
    }
    section_values = {
        name: _items(name, [item.name for item in section_items(existing, name)] or defaults)
        for name, defaults in section_defaults.items()
    }
    profile = UserProfile(
        updated_at=datetime.now(timezone.utc).isoformat(),
        summary=_ask("Longer-term development direction", existing.summary or settings.LEARNING_ANCHOR),
        knowledge_notes=_ask("Extra context about your experience", existing.knowledge_notes or settings.LEARNING_PROFILE),
        sections=existing.sections,
        evidence=existing.evidence,
        profile_changes=existing.profile_changes,
        processed_evidence_ids=existing.processed_evidence_ids,
    )
    for name, values in section_values.items():
        _update_section(profile, name, values)
    if save:
        write_profile(profile_path, profile)
        print(f"Saved profile: {profile_path}")
    return profile


def _saved_digests(start: date, end: date) -> list[tuple[date, Path]]:
    found = []
    for path in sorted((ROOT / "data" / "digests").glob("pulse_digest_*.md")):
        day = digest_date(path)
        if day is not None and start <= day <= end:
            found.append((day, path))
    return found


def _choose_digests(paths: list[str], today: date | None = None) -> list[dict]:
    today = today or datetime.now(timezone.utc).date()
    start, end, week = week_window(today)
    if paths:
        selected = []
        for value in paths:
            path = Path(value).expanduser()
            day = digest_date(path)
            if day is None or not start <= day <= end:
                raise ValueError(f"Digest {path} is outside PulseDev's {start} through {end} weekly window.")
            selected.append({"date": day.isoformat(), "content": path.read_text(encoding="utf-8")})
        return selected
    available = _saved_digests(start, end)
    if not available:
        raise RuntimeError(f"No local Pulse digests found for {week} ({start} through {end}).")
    print(f"Saved digests for {week} ({start} through {end}):")
    for index, (day, path) in enumerate(available, start=1):
        print(f"  {index}. {day.isoformat()}  {path}")
    default = ",".join(str(index) for index in range(1, len(available) + 1))
    selection = input(f"Choose weekly digest numbers, comma-separated [all: {default}]: ").strip() or default
    indices = [int(value.strip()) - 1 for value in selection.split(",")]
    chosen = [available[index] for index in indices if 0 <= index < len(available)]
    if not chosen:
        raise RuntimeError("No valid digests were selected.")
    return [{"date": day.isoformat(), "content": path.read_text(encoding="utf-8")} for day, path in chosen]


def _preview(profile: UserProfile, digests: list[dict], picks: list[dict], invoke: bool, dry_run: bool, force_picker: bool) -> None:
    policy = preview_weekly_policy(picks)
    print(f"System policy would: {policy['action']}{' (lower-friction pick)' if policy.get('lower_friction') else ''}.")
    if policy["action"] in {"resend", "carry"} and not force_picker:
        print("No new picker call is needed for the current open pick. Use --force-picker to inspect new candidates anyway.")
        return
    blocked = []
    for pick in picks:
        if pick["status"] not in {"skipped", "lapsed"} or not pick.get("proposed_at"):
            continue
        proposed = date.fromisoformat(str(pick["proposed_at"])[:10])
        blocked.append({
            "title": pick["title"], "reason": pick.get("skip_reason", pick["status"]),
            "avoid_until": (proposed + timedelta(weeks=3)).isoformat(),
        })
    pending_evidence = pending_profile_evidence(profile)
    prompt = build_picker_prompt(
        digests, profile, blocked_topics=blocked,
        lower_friction=policy.get("lower_friction", False),
        pending_evidence=pending_evidence,
    )
    if not invoke:
        print("Prompt preview (no LLM call, repo write, or email):\n")
        print(prompt)
        if dry_run:
            return
        if input("Call the model now? [y/N]: ").strip().lower() not in {"y", "yes"}:
            return
    proposal = choose_pick(prompt)
    print("\nCandidates:\n")
    for index, candidate in enumerate(proposal["candidates"]):
        marker = "SELECTED" if index == proposal["selected_index"] else "candidate"
        print(f"[{marker}] {candidate['title']}")
        print(f"  Why: {candidate['rationale']}")
    selected_pick = proposal["selected_pick"]
    print("\nSelected pick details:")
    print(f"  Outcome: {selected_pick['outcome']}")
    print(f"  First step: {selected_pick['first_step']}")
    print("  Core ideas:")
    for idea in selected_pick["core_ideas"]:
        print(f"    - {idea}")
    print(f"\nSelection: {proposal['selection_reason']}")
    print("\nProfile additions:")
    if proposal.get("profile_additions"):
        for addition in proposal["profile_additions"]:
            print(f"  {addition['type']} -> {addition['item_name']}: {addition['reasoning']}")
    else:
        print("  No profile changes proposed.")
    print("\nPreview only: nothing was committed or emailed.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="pulsedev", description="Configure or preview PulseDev locally.")
    commands = parser.add_subparsers(dest="command", required=True)
    profile_command = commands.add_parser("profile-init", help="Create or update the learning profile")
    profile_command.add_argument("--learning-log", help="Path to a local learning-log checkout")
    preview_command = commands.add_parser("preview", help="Preview or invoke the picker without repo writes")
    preview_command.add_argument("--learning-log", help="Path to a local learning-log checkout")
    preview_command.add_argument("--digest", action="append", default=[], help="Digest file from the previous Monday-Sunday window; repeat to select multiple")
    preview_command.add_argument("--invoke", action="store_true", help="Call Gemini immediately after building the prompt")
    preview_command.add_argument("--dry-run", action="store_true", help="Print the exact prompt without calling Gemini")
    preview_command.add_argument("--force-picker", action="store_true", help="Preview new candidates even when policy would resend/carry an open pick")
    args = parser.parse_args()

    if args.command == "profile-init":
        _profile_init(_learning_path(args.learning_log))
        return

    learning_path = _learning_path(args.learning_log)
    profile_file = learning_path / "profile.json"
    if not profile_file.exists():
        print("No profile found; enter a temporary profile for this preview. Use profile-init to save it.")
        profile = _profile_init(learning_path, save=False)
    else:
        profile = read_profile(profile_file)
    picks = [_parse_pick(path) for path in sorted((learning_path / "picks").glob("*/pick.md"))]
    profile = sync_completed_evidence(profile, picks)
    digests = _choose_digests(args.digest)
    _preview(profile, digests, picks, invoke=args.invoke and not args.dry_run, dry_run=args.dry_run, force_picker=args.force_picker)


if __name__ == "__main__":
    main()
