"""Shared pytest fixtures for penpen tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bot.config import Config


@pytest.fixture
def tmp_media(tmp_path: Path) -> Path:
    """Create a fresh media/ directory in tmp_path."""
    media = tmp_path / "media"
    media.mkdir()
    (media / ".gitkeep").touch()
    return media


@pytest.fixture
def sample_config() -> Config:
    """A Config with fake but structurally valid values."""
    return Config(
        bot_token="1234567890:AAFakeTokenForTesting",
        channels={"toto": "-1001404339876", "test": "-1002780029395"},
        chats={"cat": "-1001280437635"},
        admin_chat_id="29781159",
        log_level="INFO",
    )
