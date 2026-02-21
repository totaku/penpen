"""Tests for bot/config.py."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from bot.config import Config, ConfigError, load_config


def _env(**kwargs: str) -> dict[str, str]:
    """Build a minimal valid env dict."""
    base = {"BOT_TOKEN": "9999:AAFakeToken"}
    base.update(kwargs)
    return base


class TestLoadConfig:
    def test_channel_id_parsed(self) -> None:
        env = _env(CHANNEL_ID_TOTO="-1001404339876")
        with patch.dict(os.environ, env, clear=True):
            cfg = load_config()
        assert cfg.channels["toto"] == "-1001404339876"

    def test_chat_parsed(self) -> None:
        env = _env(CHAT_CAT="-1001280437635")
        with patch.dict(os.environ, env, clear=True):
            cfg = load_config()
        assert cfg.chats["cat"] == "-1001280437635"

    def test_missing_bot_token_raises(self) -> None:
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("bot.config.find_dotenv", return_value=""),
            pytest.raises(ConfigError, match="BOT_TOKEN"),
        ):
            load_config()

    def test_invalid_channel_id_raises(self) -> None:
        env = _env(CHANNEL_ID_NERD="not-a-valid-id")
        with (
            patch.dict(os.environ, env, clear=True),
            pytest.raises(ConfigError, match="Invalid channel ID"),
        ):
            load_config()

    def test_invalid_channel_id_must_start_with_minus100(self) -> None:
        env = _env(CHANNEL_ID_NERD="-9991234")
        with (
            patch.dict(os.environ, env, clear=True),
            pytest.raises(ConfigError, match="Invalid channel ID"),
        ):
            load_config()

    def test_admin_chat_id_not_in_chats(self) -> None:
        env = _env(ADMIN_CHAT_ID="12345678")
        with patch.dict(os.environ, env, clear=True):
            cfg = load_config()
        assert "admin_chat_id" not in cfg.chats
        assert cfg.admin_chat_id == "12345678"

    def test_multiple_channels(self) -> None:
        env = _env(
            CHANNEL_ID_TEST="-1002780029395",
            CHANNEL_ID_NERD="-1001271082628",
        )
        with patch.dict(os.environ, env, clear=True):
            cfg = load_config()
        assert "test" in cfg.channels
        assert "nerd" in cfg.channels

    def test_log_level_default(self) -> None:
        with patch.dict(os.environ, _env(), clear=True):
            cfg = load_config()
        assert cfg.log_level == "INFO"

    def test_log_level_custom(self) -> None:
        env = _env(LOG_LEVEL="DEBUG")
        with patch.dict(os.environ, env, clear=True):
            cfg = load_config()
        assert cfg.log_level == "DEBUG"


class TestResolveTargets:
    def test_resolve_channel(self, sample_config: Config) -> None:
        result = sample_config.resolve_targets(["toto"])
        assert result == [("toto", "-1001404339876")]

    def test_resolve_chat(self, sample_config: Config) -> None:
        result = sample_config.resolve_targets(["cat"])
        assert result == [("cat", "-1001280437635")]

    def test_resolve_multiple(self, sample_config: Config) -> None:
        result = sample_config.resolve_targets(["toto", "cat"])
        assert result == [
            ("toto", "-1001404339876"),
            ("cat", "-1001280437635"),
        ]

    def test_unknown_target_raises(self, sample_config: Config) -> None:
        with pytest.raises(ValueError, match="Unknown target 'nonexistent'"):
            sample_config.resolve_targets(["nonexistent"])

    def test_channels_searched_before_chats(self) -> None:
        cfg = Config(
            bot_token="x",
            channels={"shared": "-1001111111111"},
            chats={"shared": "-1002222222222"},
            admin_chat_id=None,
            log_level="INFO",
        )
        result = cfg.resolve_targets(["shared"])
        assert result[0][1] == "-1001111111111"
