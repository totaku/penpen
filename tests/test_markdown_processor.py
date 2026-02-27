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
    render_template,
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


class TestRenderTemplate:
    def test_basic_render(self, tmp_path: Path) -> None:
        tpl = tmp_path / "tpl.md"
        tpl.write_text("Hello {{ name }}!", encoding="utf-8")
        data = tmp_path / "data.yml"
        data.write_text("name: World", encoding="utf-8")
        assert render_template(tpl, data) == "Hello World!"

    def test_for_loop(self, tmp_path: Path) -> None:
        tpl = tmp_path / "tpl.md"
        tpl.write_text("{% for game in games %}{{ game }}\n{% endfor %}", encoding="utf-8")
        data = tmp_path / "data.yml"
        data.write_text("games:\n  - Game A\n  - Game B", encoding="utf-8")
        result = render_template(tpl, data)
        assert "Game A" in result
        assert "Game B" in result

    def test_optional_block(self, tmp_path: Path) -> None:
        tpl = tmp_path / "tpl.md"
        tpl.write_text(
            "Base{% if extra %}\nExtra: {{ extra }}{% endif %}",
            encoding="utf-8",
        )
        data_with = tmp_path / "with.yml"
        data_with.write_text("extra: bonus", encoding="utf-8")
        data_without = tmp_path / "without.yml"
        data_without.write_text("{}", encoding="utf-8")

        result_with = render_template(tpl, data_with)
        assert "Extra: bonus" in result_with

        result_without = render_template(tpl, data_without)
        assert "Extra" not in result_without

    def test_missing_template(self, tmp_path: Path) -> None:
        data = tmp_path / "data.yml"
        data.write_text("name: World", encoding="utf-8")
        with pytest.raises(MessageError, match="Template file not found"):
            render_template(tmp_path / "nonexistent.md", data)

    def test_missing_data(self, tmp_path: Path) -> None:
        tpl = tmp_path / "tpl.md"
        tpl.write_text("Hello {{ name }}!", encoding="utf-8")
        with pytest.raises(MessageError, match="Data file not found"):
            render_template(tpl, tmp_path / "nonexistent.yml")

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        tpl = tmp_path / "tpl.md"
        tpl.write_text("Hello!", encoding="utf-8")
        data = tmp_path / "data.yml"
        data.write_text("key: [unclosed", encoding="utf-8")
        with pytest.raises(MessageError, match="Invalid YAML"):
            render_template(tpl, data)

    def test_template_error(self, tmp_path: Path) -> None:
        tpl = tmp_path / "tpl.md"
        tpl.write_text("{% for %}", encoding="utf-8")
        data = tmp_path / "data.yml"
        data.write_text("{}", encoding="utf-8")
        with pytest.raises(MessageError, match="Template render error"):
            render_template(tpl, data)
