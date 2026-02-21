"""Markdown processing for Telegram messages."""

from __future__ import annotations

from pathlib import Path

import telegramify_markdown

MAX_CAPTION_LENGTH = 1024
MAX_MESSAGE_LENGTH = 4096


class MessageError(Exception):
    """Raised when message file cannot be read."""


class CaptionTooLongError(Exception):
    """Raised when caption exceeds Telegram's 1024 character limit."""

    def __init__(self, length: int) -> None:
        self.length = length
        super().__init__(
            f"Caption is {length} characters, exceeds maximum of {MAX_CAPTION_LENGTH}."
        )


def read_message(message_file: Path) -> str:
    """Read message content from file.

    Raises MessageError if file does not exist or cannot be read.
    """
    if not message_file.exists():
        raise MessageError(f"Message file not found: {message_file}")

    try:
        return message_file.read_text(encoding="utf-8")
    except OSError as e:
        raise MessageError(f"Cannot read message file {message_file}: {e}") from e


def to_telegram_markdown(text: str) -> str:
    """Convert Markdown text to Telegram MarkdownV2 format."""
    return telegramify_markdown.markdownify(text)


def prepare_caption(message_file: Path) -> str:
    """Read message file and convert to Telegram MarkdownV2 caption.

    Raises MessageError if file is missing.
    Raises CaptionTooLongError if converted text exceeds 1024 chars.
    """
    raw = read_message(message_file)
    converted = to_telegram_markdown(raw)
    if len(converted) > MAX_CAPTION_LENGTH:
        raise CaptionTooLongError(len(converted))
    return converted


def prepare_text(message_file: Path) -> str:
    """Read message file and convert to Telegram MarkdownV2 text message.

    For text-only messages (no media), limit is 4096 chars.
    Raises MessageError if file is missing.
    """
    raw = read_message(message_file)
    return to_telegram_markdown(raw)
