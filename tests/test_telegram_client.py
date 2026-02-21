"""Tests for bot/telegram_client.py (aiogram 3)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError

from bot.telegram_client import SendResult, TelegramClient, TelegramError

FAKE_TOKEN = "9999:AAFakeTokenForTesting"


class TestSendText:
    async def test_send_text_calls_send_message(self, mocker: object) -> None:
        mock = mocker.patch.object(Bot, "send_message", new_callable=AsyncMock)
        mock.return_value = MagicMock(message_id=1)

        async with TelegramClient(FAKE_TOKEN) as client:
            result = await client.send_text("-100123", "Hello world")

        mock.assert_called_once()
        assert result["ok"] is True

    async def test_send_text_passes_correct_args(self, mocker: object) -> None:
        mock = mocker.patch.object(Bot, "send_message", new_callable=AsyncMock)
        mock.return_value = MagicMock(message_id=1)

        async with TelegramClient(FAKE_TOKEN) as client:
            await client.send_text("-100123", "Hello")

        call_kwargs = mock.call_args.kwargs
        assert call_kwargs["chat_id"] == "-100123"
        assert call_kwargs["text"] == "Hello"

    async def test_send_text_telegram_error(self, mocker: object) -> None:
        mocker.patch.object(
            Bot,
            "send_message",
            side_effect=TelegramBadRequest(method="sendMessage", message="chat not found"),
        )

        async with TelegramClient(FAKE_TOKEN) as client:
            with pytest.raises(TelegramError) as exc_info:
                await client.send_text("-100123", "Hello")

        assert "chat not found" in exc_info.value.description


class TestSendVideo:
    async def test_send_video_calls_send_video(self, mocker: object, tmp_path: Path) -> None:
        video = tmp_path / "test.mp4"
        video.write_bytes(b"fake video data")

        mock = mocker.patch.object(Bot, "send_video", new_callable=AsyncMock)
        mock.return_value = MagicMock(message_id=2)

        async with TelegramClient(FAKE_TOKEN) as client:
            result = await client.send_video("-100123", video, caption="Test caption")

        mock.assert_called_once()
        assert result["ok"] is True

    async def test_send_video_with_cover(self, mocker: object, tmp_path: Path) -> None:
        video = tmp_path / "test.mp4"
        video.write_bytes(b"fake video")
        cover = tmp_path / "cover.jpg"
        cover.write_bytes(b"fake jpeg")

        mock = mocker.patch.object(Bot, "send_video", new_callable=AsyncMock)
        mock.return_value = MagicMock(message_id=3)

        async with TelegramClient(FAKE_TOKEN) as client:
            result = await client.send_video("-100123", video, caption="Cap", cover=cover)

        mock.assert_called_once()
        assert result["ok"] is True
        call_kwargs = mock.call_args.kwargs
        assert call_kwargs["cover"] is not None

    async def test_send_video_no_cover(self, mocker: object, tmp_path: Path) -> None:
        video = tmp_path / "test.mp4"
        video.write_bytes(b"fake video")

        mock = mocker.patch.object(Bot, "send_video", new_callable=AsyncMock)
        mock.return_value = MagicMock(message_id=4)

        async with TelegramClient(FAKE_TOKEN) as client:
            await client.send_video("-100123", video, caption="Cap")

        call_kwargs = mock.call_args.kwargs
        assert call_kwargs["cover"] is None


class TestRetryLogic:
    async def test_retries_on_network_error(self, mocker: object) -> None:
        call_count = 0

        async def flaky(**kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TelegramNetworkError(method="sendMessage", message="")
            return MagicMock(message_id=1)

        mocker.patch.object(Bot, "send_message", side_effect=flaky)
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        async with TelegramClient(FAKE_TOKEN) as client:
            result = await client.send_text("-100123", "Hello")

        assert call_count == 3
        assert result["ok"] is True

    async def test_raises_after_max_retries(self, mocker: object) -> None:
        async def always_fail(**kwargs: object) -> None:
            raise TelegramNetworkError(method="sendMessage", message="always fails")

        mocker.patch.object(Bot, "send_message", side_effect=always_fail)
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        async with TelegramClient(FAKE_TOKEN) as client:
            with pytest.raises(TelegramNetworkError):
                await client.send_text("-100123", "Hello")

    async def test_telegram_error_not_retried(self, mocker: object) -> None:
        call_count = 0

        async def mock_send(**kwargs: object) -> None:
            nonlocal call_count
            call_count += 1
            raise TelegramBadRequest(method="sendMessage", message="Forbidden")

        mocker.patch.object(Bot, "send_message", side_effect=mock_send)

        async with TelegramClient(FAKE_TOKEN) as client:
            with pytest.raises(TelegramError):
                await client.send_text("-100123", "Hello")

        assert call_count == 1  # no retries


class TestSendResult:
    def test_success_result(self) -> None:
        r = SendResult(target_name="toto", chat_id="-1001404339876", success=True)
        assert r.success
        assert r.error is None
        assert r.message_id is None

    def test_failure_result(self) -> None:
        r = SendResult(
            target_name="toto",
            chat_id="-1001404339876",
            success=False,
            error="chat not found",
        )
        assert not r.success
        assert r.error == "chat not found"

    def test_result_with_message_id(self) -> None:
        r = SendResult(target_name="toto", chat_id="-1001404339876", success=True, message_id=42)
        assert r.message_id == 42


class TestPinMessage:
    async def test_pin_message_calls_api(self, mocker: object) -> None:
        mock = mocker.patch.object(Bot, "pin_chat_message", new_callable=AsyncMock)
        mock.return_value = True

        async with TelegramClient(FAKE_TOKEN) as client:
            await client.pin_message("-100123", 194)

        mock.assert_called_once()
        call_kwargs = mock.call_args.kwargs
        assert call_kwargs["chat_id"] == "-100123"
        assert call_kwargs["message_id"] == 194

    async def test_unpin_message_calls_api(self, mocker: object) -> None:
        mock = mocker.patch.object(Bot, "unpin_chat_message", new_callable=AsyncMock)
        mock.return_value = True

        async with TelegramClient(FAKE_TOKEN) as client:
            await client.unpin_message("-100123", 194)

        mock.assert_called_once()
        call_kwargs = mock.call_args.kwargs
        assert call_kwargs["chat_id"] == "-100123"
        assert call_kwargs["message_id"] == 194


class TestDeleteMessage:
    async def test_delete_message_calls_api(self, mocker: object) -> None:
        mock = mocker.patch.object(Bot, "delete_message", new_callable=AsyncMock)
        mock.return_value = True

        async with TelegramClient(FAKE_TOKEN) as client:
            await client.delete_message("-100123", 194)

        mock.assert_called_once()
        call_kwargs = mock.call_args.kwargs
        assert call_kwargs["chat_id"] == "-100123"
        assert call_kwargs["message_id"] == 194


class TestEditMessage:
    async def test_edit_message_text_calls_api(self, mocker: object) -> None:
        mock = mocker.patch.object(Bot, "edit_message_text", new_callable=AsyncMock)
        mock.return_value = MagicMock(message_id=194)

        async with TelegramClient(FAKE_TOKEN) as client:
            result = await client.edit_message_text("-100123", 194, "New text")

        mock.assert_called_once()
        call_kwargs = mock.call_args.kwargs
        assert call_kwargs["chat_id"] == "-100123"
        assert call_kwargs["message_id"] == 194
        assert call_kwargs["text"] == "New text"
        assert result["ok"] is True
        assert result["result"]["message_id"] == 194

    async def test_edit_message_caption_calls_api(self, mocker: object) -> None:
        mock = mocker.patch.object(Bot, "edit_message_caption", new_callable=AsyncMock)
        mock.return_value = MagicMock(message_id=194)

        async with TelegramClient(FAKE_TOKEN) as client:
            result = await client.edit_message_caption("-100123", 194, "New caption")

        mock.assert_called_once()
        call_kwargs = mock.call_args.kwargs
        assert call_kwargs["chat_id"] == "-100123"
        assert call_kwargs["message_id"] == 194
        assert call_kwargs["caption"] == "New caption"
        assert result["ok"] is True


class TestReplyTo:
    async def test_send_text_with_reply_parameters(self, mocker: object) -> None:
        mock = mocker.patch.object(Bot, "send_message", new_callable=AsyncMock)
        mock.return_value = MagicMock(message_id=200)

        async with TelegramClient(FAKE_TOKEN) as client:
            result = await client.send_text("-100123", "Reply!", reply_to_message_id=194)

        mock.assert_called_once()
        call_kwargs = mock.call_args.kwargs
        assert call_kwargs["reply_parameters"] is not None
        assert call_kwargs["reply_parameters"].message_id == 194
        assert result["ok"] is True

    async def test_send_text_without_reply(self, mocker: object) -> None:
        mock = mocker.patch.object(Bot, "send_message", new_callable=AsyncMock)
        mock.return_value = MagicMock(message_id=201)

        async with TelegramClient(FAKE_TOKEN) as client:
            await client.send_text("-100123", "No reply")

        call_kwargs = mock.call_args.kwargs
        assert call_kwargs["reply_parameters"] is None
