"""Tests for bot/markdown_processor.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from bot.markdown_processor import (
    MAX_CAPTION_LENGTH,
    CaptionTooLongError,
    MessageError,
    prepare_caption,
    prepare_text,
    read_message,
    to_telegram_markdown,
)


class TestReadMessage:
    def test_reads_utf8_file(self, tmp_path: Path) -> None:
        msg = tmp_path / "message.md"
        msg.write_text("Привет мир!\n**bold**", encoding="utf-8")
        content = read_message(msg)
        assert "Привет мир!" in content

    def test_missing_file_raises_message_error(self, tmp_path: Path) -> None:
        with pytest.raises(MessageError, match="not found"):
            read_message(tmp_path / "nonexistent.md")

    def test_returns_full_content(self, tmp_path: Path) -> None:
        msg = tmp_path / "message.md"
        text = "Line 1\nLine 2\nLine 3"
        msg.write_text(text, encoding="utf-8")
        assert read_message(msg) == text


class TestToTelegramMarkdown:
    def test_returns_string(self) -> None:
        result = to_telegram_markdown("Hello **world**")
        assert isinstance(result, str)

    def test_converts_bold(self) -> None:
        result = to_telegram_markdown("**bold**")
        assert "bold" in result


class TestPrepareCaption:
    def test_valid_caption(self, tmp_path: Path) -> None:
        msg = tmp_path / "message.md"
        msg.write_text("Short message", encoding="utf-8")
        caption = prepare_caption(msg)
        assert isinstance(caption, str)
        assert len(caption) <= MAX_CAPTION_LENGTH

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(MessageError):
            prepare_caption(tmp_path / "missing.md")

    def test_too_long_raises_caption_too_long(self, tmp_path: Path) -> None:
        msg = tmp_path / "message.md"
        # Write raw text that will be long enough after conversion
        long_text = "a" * (MAX_CAPTION_LENGTH + 100)
        msg.write_text(long_text, encoding="utf-8")
        with pytest.raises(CaptionTooLongError) as exc_info:
            prepare_caption(msg)
        assert exc_info.value.length > MAX_CAPTION_LENGTH


class TestPrepareText:
    def test_returns_string(self, tmp_path: Path) -> None:
        msg = tmp_path / "message.md"
        msg.write_text("Hello world", encoding="utf-8")
        result = prepare_text(msg)
        assert isinstance(result, str)

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(MessageError):
            prepare_text(tmp_path / "missing.md")
