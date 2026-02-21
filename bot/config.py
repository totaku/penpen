"""Configuration loading and validation for penpen bot."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""


@dataclass(frozen=True)
class Config:
    bot_token: str
    channels: dict[str, str]  # {"toto": "-1001404339876"}
    chats: dict[str, str]  # {"cat": "-1001280437635"}
    admin_chat_id: str | None
    log_level: str

    def resolve_targets(self, names: list[str]) -> list[tuple[str, str]]:
        """Resolve target names to (name, chat_id) pairs.

        Searches channels first, then chats. Raises ValueError for unknown names.
        """
        results: list[tuple[str, str]] = []
        for name in names:
            if name in self.channels:
                results.append((name, self.channels[name]))
            elif name in self.chats:
                results.append((name, self.chats[name]))
            else:
                known = sorted(list(self.channels) + list(self.chats))
                raise ValueError(f"Unknown target '{name}'. Known targets: {known}")
        return results


_CHANNEL_ID_PATTERN = re.compile(r"^CHANNEL_ID_(.+)$")
_CHAT_PATTERN = re.compile(r"^CHAT_(.+)$")
_VALID_CHANNEL_ID_RE = re.compile(r"^-100\d+$")
_VALID_CHAT_ID_RE = re.compile(r"^-?\d+$")


def _validate_channel_id(name: str, value: str) -> None:
    """Validate that a channel ID matches expected Telegram format (-100...)."""
    if not _VALID_CHANNEL_ID_RE.match(value):
        raise ConfigError(
            f"Invalid channel ID for '{name}': '{value}'. "
            "Channel IDs must start with -100 followed by digits."
        )


def _validate_chat_id(name: str, value: str) -> None:
    """Validate that a chat ID is a valid integer."""
    if not _VALID_CHAT_ID_RE.match(value):
        raise ConfigError(
            f"Invalid chat ID for '{name}': '{value}'. Chat IDs must be integers."
        )


def load_config() -> Config:
    """Load configuration from .env file and environment variables.

    Uses find_dotenv() to locate the .env file automatically.
    Raises ConfigError if required variables are missing or invalid.
    """
    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path)

    bot_token = os.environ.get("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ConfigError("BOT_TOKEN is required but not set in environment or .env file.")

    channels: dict[str, str] = {}
    chats: dict[str, str] = {}

    for key, value in os.environ.items():
        value = value.strip()

        channel_match = _CHANNEL_ID_PATTERN.match(key)
        if channel_match:
            channel_name = channel_match.group(1).lower()
            _validate_channel_id(key, value)
            channels[channel_name] = value
            continue

        chat_match = _CHAT_PATTERN.match(key)
        if chat_match:
            chat_name = chat_match.group(1).lower()
            # Skip ADMIN_CHAT_ID — it's not a target
            if key == "ADMIN_CHAT_ID":
                continue
            _validate_chat_id(key, value)
            chats[chat_name] = value

    admin_chat_id = os.environ.get("ADMIN_CHAT_ID", "").strip() or None
    log_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper()

    return Config(
        bot_token=bot_token,
        channels=channels,
        chats=chats,
        admin_chat_id=admin_chat_id,
        log_level=log_level,
    )
