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

    def __init__(self, length: int, overflow_raw: str) -> None:
        self.length = length
        self.overflow_raw = overflow_raw
        super().__init__(
            f"Caption is {length} characters, exceeds maximum of {MAX_CAPTION_LENGTH}."
        )


class TextTooLongError(Exception):
    """Raised when text-only message exceeds Telegram's 4096 character limit."""

    def __init__(self, length: int, overflow_raw: str) -> None:
        self.length = length
        self.overflow_raw = overflow_raw
        super().__init__(
            f"Message is {length} characters, exceeds maximum of {MAX_MESSAGE_LENGTH}."
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


def _find_overflow_raw(raw: str, limit: int) -> str:
    """Return the part of raw markdown that didn't fit within the converted limit.

    Splits by paragraphs, converts each to MarkdownV2, accumulates length,
    and returns the raw paragraphs that exceed the limit.
    """
    paragraphs = raw.split("\n\n")
    accumulated = 0
    for i, para in enumerate(paragraphs):
        converted_para = to_telegram_markdown(para)
        addition = len(converted_para) + (2 if i > 0 else 0)
        if accumulated + addition > limit:
            return "\n\n".join(paragraphs[i:])
        accumulated += addition
    return ""


def prepare_caption_from_str(raw: str) -> str:
    """Convert raw markdown string to Telegram MarkdownV2 caption.

    Raises CaptionTooLongError if converted text exceeds 1024 chars.
    """
    converted = to_telegram_markdown(raw)
    if len(converted) > MAX_CAPTION_LENGTH:
        raise CaptionTooLongError(len(converted), _find_overflow_raw(raw, MAX_CAPTION_LENGTH))
    return converted


def prepare_text_from_str(raw: str) -> str:
    """Convert raw markdown string to Telegram MarkdownV2 text message.

    For text-only messages (no media), limit is 4096 chars.
    Raises TextTooLongError if converted text exceeds 4096 chars.
    """
    converted = to_telegram_markdown(raw)
    if len(converted) > MAX_MESSAGE_LENGTH:
        raise TextTooLongError(len(converted), _find_overflow_raw(raw, MAX_MESSAGE_LENGTH))
    return converted


def prepare_caption(message_file: Path) -> str:
    """Read message file and convert to Telegram MarkdownV2 caption.

    Raises MessageError if file is missing.
    Raises CaptionTooLongError if converted text exceeds 1024 chars.
    """
    return prepare_caption_from_str(read_message(message_file))


def prepare_text(message_file: Path) -> str:
    """Read message file and convert to Telegram MarkdownV2 text message.

    For text-only messages (no media), limit is 4096 chars.
    Raises MessageError if file is missing.
    Raises TextTooLongError if converted text exceeds 4096 chars.
    """
    return prepare_text_from_str(read_message(message_file))


def render_template(template_file: Path, data_file: Path) -> str:
    """Render a Jinja2 template with YAML data. Returns raw markdown string."""
    import yaml
    from jinja2 import Template, TemplateError

    try:
        raw_template = template_file.read_text(encoding="utf-8")
    except OSError as e:
        raise MessageError(f"Template file not found: {template_file}: {e}") from e

    try:
        data = yaml.safe_load(data_file.read_text(encoding="utf-8")) or {}
    except OSError as e:
        raise MessageError(f"Data file not found: {data_file}: {e}") from e
    except yaml.YAMLError as e:
        raise MessageError(f"Invalid YAML in {data_file}: {e}") from e

    try:
        return Template(raw_template).render(**data)
    except TemplateError as e:
        raise MessageError(f"Template render error: {e}") from e
