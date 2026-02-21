"""Persistent storage for last sent message IDs."""

from __future__ import annotations

import re
from pathlib import Path


def save_last_id(target: str, message_id: int) -> None:
    """Save message_id to .last_message_id.<target> in current directory."""
    Path(f".last_message_id.{target}").write_text(str(message_id))


def load_last_id(target: str) -> int | None:
    """Read message_id from .last_message_id.<target>, return None if not found."""
    p = Path(f".last_message_id.{target}")
    return int(p.read_text().strip()) if p.exists() else None


def parse_message_ref(value: str) -> int:
    """Parse message ID from a number string or a t.me link.

    Accepts:
        "194"                              → 194
        "https://t.me/c/1234567890/194"   → 194
    """
    if value.isdigit():
        return int(value)
    m = re.match(r"https://t\.me/c/\d+/(\d+)", value)
    if m:
        return int(m.group(1))
    raise ValueError(f"Cannot parse message reference: {value!r}")


def parse_forward_ref(value: str) -> tuple[str, int]:
    """Parse a t.me link into (from_chat_id, message_id).

    Accepts:
        "https://t.me/c/1234567890/194"  → ("-1001234567890", 194)  # private
        "https://t.me/username/194"      → ("@username", 194)        # public
    """
    # Private channel: t.me/c/<numeric_id>/<msg_id>
    m = re.match(r"https://t\.me/c/(\d+)/(\d+)", value)
    if m:
        from_chat_id = f"-100{m.group(1)}"
        message_id = int(m.group(2))
        return from_chat_id, message_id
    # Public channel: t.me/<username>/<msg_id>
    m = re.match(r"https://t\.me/([A-Za-z]\w+)/(\d+)", value)
    if m:
        from_chat_id = f"@{m.group(1)}"
        message_id = int(m.group(2))
        return from_chat_id, message_id
    raise ValueError(f"Cannot parse forward reference (expected t.me link): {value!r}")
