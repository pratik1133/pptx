from __future__ import annotations

from datetime import datetime, timezone


def format_log_event(level: str, message: str, **fields: str) -> str:
    timestamp = datetime.now(timezone.utc).isoformat()
    parts = [f"ts={timestamp}", f"level={level.upper()}", f"msg={message}"]
    parts.extend(f"{key}={value}" for key, value in fields.items())
    return " ".join(parts)
