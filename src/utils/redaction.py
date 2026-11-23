import re

from src.config.settings import settings


def redact_secrets(value: object) -> str:
    text = str(value)
    for name in ("GEMINI_API_KEY", "RESEND_API_KEY", "LEARNING_REPO_TOKEN"):
        secret = getattr(settings, name, "")
        if secret:
            text = text.replace(secret, "[REDACTED]")
    text = re.sub(r"(?i)(bearer\s+)[^\s,;]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)([?&](?:key|token|access_token)=)[^&\s]+", r"\1[REDACTED]", text)
    return text[:2000]
