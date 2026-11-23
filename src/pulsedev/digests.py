"""Calendar-window selection for PulseDev's preceding weekly digests."""

import re
from datetime import date, datetime, timedelta
from pathlib import Path


def week_window(today: date) -> tuple[date, date, str]:
    """Return the previous Monday-Sunday window and its ISO week label."""
    this_monday = today - timedelta(days=today.weekday())
    start = this_monday - timedelta(days=7)
    end = this_monday - timedelta(days=1)
    iso = start.isocalendar()
    return start, end, f"{iso.year}-w{iso.week:02d}"


def digest_date(path: Path) -> date | None:
    """Resolve a digest's UTC calendar date from its timestamped filename."""
    match = re.fullmatch(r"pulse_digest_(\d{8})T\d{6}Z", path.stem)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y%m%d").date()
    except ValueError:
        return None


def read_weekly_digests(folder: Path, start: date, end: date) -> list[dict[str, str]]:
    """Read only saved digest files whose UTC filename date is in the window."""
    selected: list[tuple[date, Path]] = []
    for path in folder.glob("pulse_digest_*.md"):
        day = digest_date(path)
        if day is not None and start <= day <= end:
            selected.append((day, path))
    return [
        {"date": day.isoformat(), "content": path.read_text(encoding="utf-8")}
        for day, path in sorted(selected, key=lambda item: (item[0], item[1].name))
    ]
