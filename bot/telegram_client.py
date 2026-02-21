"""Telegram Bot API client using aiogram 3."""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError
from aiogram.types import FSInputFile, InputMediaPhoto, Message, ReplyParameters
from aiohttp import ClientTimeout

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_BACKOFF = 1.0  # seconds

type BotMethod[**P, R] = Callable[P, Coroutine[Any, Any, R]]


class TelegramError(Exception):
    """Raised when Telegram API returns an error response."""

    def __init__(self, code: int, description: str) -> None:
        self.code = code
        self.description = description
        super().__init__(f"Telegram API error {code}: {description}")


@dataclass(frozen=True)
class SendResult:
    target_name: str
    chat_id: str
    success: bool
    error: str | None = None
    message_id: int | None = None


class TelegramClient:
    """Async Telegram Bot API client with retry logic (aiogram 3)."""

    def __init__(self, token: str) -> None:
        self._token = token
        self._bot: Bot | None = None
        self._session: AiohttpSession | None = None

    async def __aenter__(self) -> TelegramClient:
        self._session = AiohttpSession(timeout=ClientTimeout(total=300))
        self._bot = Bot(token=self._token, session=self._session)
        return self

    async def __aexit__(self, *_args: object) -> None:
        if self._bot:
            await self._bot.session.close()
            self._bot = None
            self._session = None

    async def send_text(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "MarkdownV2",
        reply_to_message_id: int | None = None,
    ) -> dict[str, Any]:
        """Send a text message."""
        assert self._bot is not None, "Client not initialized — use as async context manager"
        pm = ParseMode.MARKDOWN_V2 if parse_mode == "MarkdownV2" else parse_mode
        reply_params = (
            ReplyParameters(message_id=reply_to_message_id) if reply_to_message_id else None
        )
        result: Message = await self._with_retry(
            self._bot.send_message,
            chat_id=chat_id,
            text=text,
            parse_mode=pm,
            reply_parameters=reply_params,
        )
        return {"ok": True, "result": {"message_id": result.message_id}}

    async def send_photo(
        self,
        chat_id: str,
        photo: Path,
        caption: str,
        parse_mode: str = "MarkdownV2",
        reply_to_message_id: int | None = None,
    ) -> dict[str, Any]:
        """Send a single photo with caption."""
        assert self._bot is not None, "Client not initialized — use as async context manager"
        pm = ParseMode.MARKDOWN_V2 if parse_mode == "MarkdownV2" else parse_mode
        reply_params = (
            ReplyParameters(message_id=reply_to_message_id) if reply_to_message_id else None
        )
        result: Message = await self._with_retry(
            self._bot.send_photo,
            chat_id=chat_id,
            photo=FSInputFile(photo),
            caption=caption,
            parse_mode=pm,
            reply_parameters=reply_params,
        )
        return {"ok": True, "result": {"message_id": result.message_id}}

    async def send_media_group(
        self,
        chat_id: str,
        photos: list[Path],
        caption: str,
        parse_mode: str = "MarkdownV2",
        reply_to_message_id: int | None = None,
    ) -> dict[str, Any]:
        """Send a group of photos (2-10) with caption on the first."""
        assert self._bot is not None, "Client not initialized — use as async context manager"
        pm = ParseMode.MARKDOWN_V2 if parse_mode == "MarkdownV2" else parse_mode
        media: list[InputMediaPhoto] = [
            InputMediaPhoto(media=FSInputFile(p)) for p in photos
        ]
        media[0] = InputMediaPhoto(
            media=FSInputFile(photos[0]),
            caption=caption,
            parse_mode=pm,
        )
        reply_params = (
            ReplyParameters(message_id=reply_to_message_id) if reply_to_message_id else None
        )
        results: list[Message] = await self._with_retry(
            self._bot.send_media_group,
            chat_id=chat_id,
            media=media,
            reply_parameters=reply_params,
        )
        first = results[0] if isinstance(results, list) else results
        return {"ok": True, "result": {"message_id": first.message_id}}

    async def send_video(
        self,
        chat_id: str,
        video: Path,
        caption: str,
        cover: Path | None = None,
        width: int = 1280,
        height: int = 720,
        duration: int = 0,
        parse_mode: str = "MarkdownV2",
        reply_to_message_id: int | None = None,
    ) -> dict[str, Any]:
        """Send a video with optional cover image.

        Uses `cover` (not `thumbnail`) — no 320px size limit, supports streaming preview.
        """
        assert self._bot is not None, "Client not initialized — use as async context manager"
        pm = ParseMode.MARKDOWN_V2 if parse_mode == "MarkdownV2" else parse_mode
        reply_params = (
            ReplyParameters(message_id=reply_to_message_id) if reply_to_message_id else None
        )
        result: Message = await self._with_retry(
            self._bot.send_video,
            chat_id=chat_id,
            video=FSInputFile(video),
            caption=caption,
            cover=FSInputFile(cover) if cover else None,
            width=width,
            height=height,
            duration=duration,
            supports_streaming=True,
            parse_mode=pm,
            reply_parameters=reply_params,
        )
        return {"ok": True, "result": {"message_id": result.message_id}}

    async def pin_message(self, chat_id: str, message_id: int) -> None:
        """Pin a message in a chat."""
        assert self._bot is not None, "Client not initialized — use as async context manager"
        await self._with_retry(
            self._bot.pin_chat_message,
            chat_id=chat_id,
            message_id=message_id,
        )

    async def unpin_message(self, chat_id: str, message_id: int) -> None:
        """Unpin a message in a chat."""
        assert self._bot is not None, "Client not initialized — use as async context manager"
        await self._with_retry(
            self._bot.unpin_chat_message,
            chat_id=chat_id,
            message_id=message_id,
        )

    async def delete_message(self, chat_id: str, message_id: int) -> None:
        """Delete a message."""
        assert self._bot is not None, "Client not initialized — use as async context manager"
        await self._with_retry(
            self._bot.delete_message,
            chat_id=chat_id,
            message_id=message_id,
        )

    async def edit_message_text(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        parse_mode: str = "MarkdownV2",
    ) -> dict[str, Any]:
        """Edit text of an existing message."""
        assert self._bot is not None, "Client not initialized — use as async context manager"
        pm = ParseMode.MARKDOWN_V2 if parse_mode == "MarkdownV2" else parse_mode
        result: Message = await self._with_retry(
            self._bot.edit_message_text,
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode=pm,
        )
        return {"ok": True, "result": {"message_id": result.message_id}}

    async def edit_message_caption(
        self,
        chat_id: str,
        message_id: int,
        caption: str,
        parse_mode: str = "MarkdownV2",
    ) -> dict[str, Any]:
        """Edit caption of a message with media (photo/video/document)."""
        assert self._bot is not None, "Client not initialized — use as async context manager"
        pm = ParseMode.MARKDOWN_V2 if parse_mode == "MarkdownV2" else parse_mode
        result: Message = await self._with_retry(
            self._bot.edit_message_caption,
            chat_id=chat_id,
            message_id=message_id,
            caption=caption,
            parse_mode=pm,
        )
        return {"ok": True, "result": {"message_id": result.message_id}}

    async def _with_retry(
        self,
        method: Callable[..., Coroutine[Any, Any, Any]],
        **kwargs: Any,
    ) -> Any:
        """Call an aiogram Bot method with retry logic.

        Retries on: TelegramNetworkError, TimeoutError, OSError.
        Does NOT retry on: TelegramAPIError (logic errors from API).
        """
        last_exc: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                coro = method(**kwargs)
                if inspect.isawaitable(coro):
                    return await coro
                return coro
            except TelegramNetworkError as e:
                # Network-level error — retry
                last_exc = e
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_BACKOFF * (2**attempt)
                    logger.warning(
                        "Attempt %d failed: %s. Retrying in %.1fs…", attempt + 1, e, delay
                    )
                    await asyncio.sleep(delay)
            except TelegramAPIError as e:
                # API logic error — do not retry, wrap and raise
                raise TelegramError(
                    code=0,
                    description=str(e.message) if hasattr(e, "message") else str(e),
                ) from e
            except (TimeoutError, OSError) as e:
                last_exc = e
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_BACKOFF * (2**attempt)
                    logger.warning(
                        "Attempt %d failed: %s. Retrying in %.1fs…", attempt + 1, e, delay
                    )
                    await asyncio.sleep(delay)

        raise last_exc or RuntimeError("All retries exhausted")
