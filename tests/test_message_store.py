"""Tests for bot/message_store.py."""

from __future__ import annotations

import pytest

from bot.message_store import load_last_id, parse_forward_ref, parse_message_ref, save_last_id


class TestSaveAndLoad:
    def test_round_trip(self, tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)  # type: ignore[arg-type]
        save_last_id("toto", 194)
        assert load_last_id("toto") == 194

    def test_overwrites_previous(self, tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)  # type: ignore[arg-type]
        save_last_id("toto", 100)
        save_last_id("toto", 200)
        assert load_last_id("toto") == 200

    def test_different_targets_isolated(
        self, tmp_path: object, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)  # type: ignore[arg-type]
        save_last_id("toto", 10)
        save_last_id("test", 20)
        assert load_last_id("toto") == 10
        assert load_last_id("test") == 20


class TestLoadNonexistent:
    def test_returns_none_when_missing(
        self, tmp_path: object, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)  # type: ignore[arg-type]
        assert load_last_id("nonexistent") is None


class TestParseMessageRef:
    def test_parse_number(self) -> None:
        assert parse_message_ref("194") == 194

    def test_parse_large_number(self) -> None:
        assert parse_message_ref("999999") == 999999

    def test_parse_url(self) -> None:
        assert parse_message_ref("https://t.me/c/1234567890/194") == 194

    def test_parse_url_different_id(self) -> None:
        assert parse_message_ref("https://t.me/c/9876543210/42") == 42

    def test_invalid_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse message reference"):
            parse_message_ref("not-a-number")

    def test_invalid_url_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse message reference"):
            parse_message_ref("https://t.me/somechannel/194")

    def test_empty_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse message reference"):
            parse_message_ref("")


class TestParseForwardRef:
    def test_parse_private_url(self) -> None:
        from_chat_id, message_id = parse_forward_ref("https://t.me/c/1234567890/194")
        assert from_chat_id == "-1001234567890"
        assert message_id == 194

    def test_prepends_minus100(self) -> None:
        from_chat_id, _ = parse_forward_ref("https://t.me/c/9876543210/42")
        assert from_chat_id == "-1009876543210"

    def test_parse_public_url(self) -> None:
        from_chat_id, message_id = parse_forward_ref("https://t.me/brknbtns/256")
        assert from_chat_id == "@brknbtns"
        assert message_id == 256

    def test_public_url_username_preserved(self) -> None:
        from_chat_id, _ = parse_forward_ref("https://t.me/durov/1")
        assert from_chat_id == "@durov"

    def test_message_id_correct(self) -> None:
        _, message_id = parse_forward_ref("https://t.me/c/1111111111/999")
        assert message_id == 999

    def test_bare_number_raises(self) -> None:
        with pytest.raises(ValueError, match="expected t.me link"):
            parse_forward_ref("194")

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="expected t.me link"):
            parse_forward_ref("")
