"""
Pulse daily runner — entry point for the scheduled cron job.

Usage:
    uv run python -m src.runner
"""

import logging
import sys
from datetime import datetime, timezone

from src.graph import pulse_graph
from src.config.profiles import TOPIC_PROFILES
from src.services.email_service import send_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("pulse.runner")


def main() -> None:
    start = datetime.now(timezone.utc)
    logger.info(f"Pulse run starting — {start.strftime('%Y-%m-%d %H:%M UTC')}")

    try:
        result = pulse_graph.invoke({"topic_profiles": TOPIC_PROFILES})
    except Exception as exc:
        logger.exception(f"Graph invocation failed: {exc}")
        sys.exit(1)

    errors: list[str] = result.get("errors", [])
    digest: str = result.get("final_digest", "")

    if errors:
        logger.warning(f"{len(errors)} non-fatal error(s) during ingestion/summarization:")
        for err in errors:
            logger.warning(f"  {err}")

    if not digest:
        logger.error("No digest produced — nothing to send.")
        sys.exit(1)

    try:
        send_digest(result)
    except RuntimeError as exc:
        # Configuration error — log clearly and exit
        logger.error(str(exc))
        sys.exit(1)
    except Exception as exc:
        logger.exception(f"Failed to send digest email: {exc}")
        sys.exit(1)

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    logger.info(f"Pulse run complete in {elapsed:.1f}s.")


if __name__ == "__main__":
    main()
