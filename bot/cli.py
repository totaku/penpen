"""CLI entry point for penpen bot."""

from __future__ import annotations

import argparse
import asyncio
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bot.config import Config, ConfigError, load_config
from bot.markdown_processor import (
    MAX_CAPTION_LENGTH,
    CaptionTooLongError,
    MessageError,
    TextTooLongError,
    prepare_caption,
    prepare_text,
)
from bot.media_scanner import MediaKind, MediaPlan, clear, scan
from bot.message_store import load_last_id, parse_forward_ref, parse_message_ref, save_last_id
from bot.telegram_client import SendResult, TelegramClient, TelegramError

DEFAULT_MESSAGE_FILE = Path("message.md")
DEFAULT_MEDIA_DIR = Path("media")


@dataclass(frozen=True)
class SendArgs:
    targets: list[str]
    video_url: str | None
    dry_run: bool
    debug: bool
    message_file: Path
    media_dir: Path
    keep_media: bool
    pin: str | None = None
    unpin: str | None = None
    delete: str | None = None
    edit: str | None = None
    reply_to: str | None = None
    forward: str | None = None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bot",
        description="Penpen — CLI Telegram bot",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    send = sub.add_parser("send", help="Send message to targets")
    send.add_argument(
        "--to",
        nargs="+",
        required=True,
        metavar="TARGET",
        dest="targets",
        help="Target name(s) from config (channel or chat)",
    )
    send.add_argument(
        "--video",
        metavar="URL",
        dest="video_url",
        default=None,
        help="YouTube URL to download and attach",
    )
    send.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print summary without sending",
    )
    send.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug logging",
    )
    send.add_argument(
        "--message",
        metavar="FILE",
        dest="message_file",
        type=Path,
        default=DEFAULT_MESSAGE_FILE,
        help=f"Path to message markdown file (default: {DEFAULT_MESSAGE_FILE})",
    )
    send.add_argument(
        "--media-dir",
        metavar="DIR",
        dest="media_dir",
        type=Path,
        default=DEFAULT_MEDIA_DIR,
        help=f"Path to media directory (default: {DEFAULT_MEDIA_DIR})",
    )
    send.add_argument(
        "--keep-media",
        action="store_true",
        default=False,
        help="Keep media files after sending",
    )
    send.add_argument(
        "--pin",
        metavar="REF",
        nargs="?",
        const="last",
        default=None,
        help="Pin message by ID or link (omit value to pin last sent)",
    )
    send.add_argument(
        "--unpin",
        metavar="REF",
        nargs="?",
        const="last",
        default=None,
        help="Unpin message by ID or link (omit value to unpin last sent)",
    )
    send.add_argument(
        "--delete",
        metavar="REF",
        nargs="?",
        const="last",
        default=None,
        help="Delete message by ID or link (omit value to delete last sent)",
    )
    send.add_argument(
        "--edit",
        metavar="REF",
        nargs="?",
        const="last",
        default=None,
        help="Edit message text by ID or link (reads from message.md)",
    )
    send.add_argument(
        "--reply-to",
        metavar="REF",
        dest="reply_to",
        nargs="?",
        const="last",
        default=None,
        help="Reply to message by ID or link (omit value to reply to last sent)",
    )
    send.add_argument(
        "--forward",
        metavar="LINK",
        default=None,
        help="Forward message by t.me/c/... link to all targets",
    )

    return parser


def _setup_logging(debug: bool, log_level: str) -> None:
    level = logging.DEBUG if debug else getattr(logging, log_level, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _get_video_dimensions(video_path: Path) -> tuple[int, int, int]:
    """Use ffprobe to get video width, height, duration. Returns (w, h, duration_secs)."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                str(video_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    w = int(stream.get("width", 1280))
                    h = int(stream.get("height", 720))
                    dur = float(stream.get("duration", 0))
                    return min(w, 1920), min(h, 1080), int(dur)
    except Exception:
        pass
    return 1280, 720, 0


async def _send_to_target(
    client: TelegramClient | None,
    target_name: str,
    chat_id: str,
    plan: MediaPlan,
    text: str,
    dry_run: bool = False,
    reply_to_message_id: int | None = None,
) -> SendResult:
    """Dispatch send based on MediaPlan kind."""
    log = logging.getLogger(__name__)

    if dry_run:
        log.info("[dry-run] Would send to %s (%s), kind=%s", target_name, chat_id, plan.kind.name)
        if reply_to_message_id:
            log.info("[dry-run] Reply to message_id=%d", reply_to_message_id)
        return SendResult(target_name=target_name, chat_id=chat_id, success=True)

    assert client is not None, "client required when not dry_run"
    try:
        resp: dict[str, Any]
        if plan.kind == MediaKind.TEXT_ONLY:
            resp = await client.send_text(
                chat_id, text, reply_to_message_id=reply_to_message_id,
            )

        elif plan.kind == MediaKind.SINGLE_PHOTO:
            resp = await client.send_photo(
                chat_id, plan.images[0], caption=text,
                reply_to_message_id=reply_to_message_id,
            )

        elif plan.kind == MediaKind.PHOTO_GROUP:
            resp = await client.send_media_group(
                chat_id, plan.images, caption=text,
                reply_to_message_id=reply_to_message_id,
            )

        elif plan.kind == MediaKind.SINGLE_VIDEO:
            video = plan.videos[0]
            width, height, duration = _get_video_dimensions(video)
            resp = await client.send_video(
                chat_id,
                video,
                caption=text,
                cover=plan.thumbnail,
                width=width,
                height=height,
                duration=duration,
                reply_to_message_id=reply_to_message_id,
            )
        else:
            resp = {}

        message_id: int | None = resp.get("result", {}).get("message_id") if resp else None
        log.info("Sent to %s (%s), message_id=%s", target_name, chat_id, message_id)
        return SendResult(
            target_name=target_name, chat_id=chat_id, success=True, message_id=message_id,
        )

    except TelegramError as e:
        log.error("Failed to send to %s: %s", target_name, e)
        return SendResult(target_name=target_name, chat_id=chat_id, success=False, error=str(e))
    except Exception as e:
        log.error("Unexpected error sending to %s: %s", target_name, e)
        return SendResult(target_name=target_name, chat_id=chat_id, success=False, error=str(e))


def _resolve_message_ref(ref: str, target: str, log: logging.Logger) -> int | None:
    """Resolve a message reference (number, link, or 'last') to a message_id."""
    if ref == "last":
        mid = load_last_id(target)
        if mid is None:
            log.error("No last message ID found for target %r", target)
            return None
        return mid
    try:
        return parse_message_ref(ref)
    except ValueError as e:
        log.error("%s", e)
        return None


async def _notify_admin(config: Config, message: str, parse_mode: str | None = None) -> None:
    """Send a notification to ADMIN_CHAT_ID if configured."""
    if not config.admin_chat_id:
        return
    async with TelegramClient(config.bot_token) as client:
        await client.notify_admin(config.admin_chat_id, message, parse_mode=parse_mode)


async def _run_send(args: SendArgs, config: Config) -> int:
    """Async implementation of the send command. Returns exit code."""
    log = logging.getLogger(__name__)

    # Resolve targets
    try:
        targets = config.resolve_targets(args.targets)
    except ValueError as e:
        log.error("%s", e)
        return 1

    # Handle --forward
    if args.forward is not None:
        try:
            from_chat_id, message_id = parse_forward_ref(args.forward)
        except ValueError as e:
            log.error("%s", e)
            await _notify_admin(config, f"penpen ошибка: {e}")
            return 1

        if args.dry_run:
            log.info(
                "[dry-run] Would forward message %d from %s to %s",
                message_id, from_chat_id, [name for name, _ in targets],
            )
            return 0

        async with TelegramClient(config.bot_token) as client:
            all_ok = True
            for target_name, chat_id in targets:
                try:
                    await client.forward_message(chat_id, from_chat_id, message_id)
                    log.info("Forwarded message %d to %s", message_id, target_name)
                except TelegramError as e:
                    log.error("Failed to forward to %s: %s", target_name, e)
                    await _notify_admin(
                        config,
                        f"penpen ошибка forward в {target_name}: {e}",
                    )
                    all_ok = False
        return 0 if all_ok else 1

    # Handle management commands (pin/unpin/delete/edit) — no media sending
    management_action = args.pin or args.unpin or args.delete or args.edit
    if management_action is not None:
        async with TelegramClient(config.bot_token) as client:
            all_ok = True
            for target_name, chat_id in targets:
                if args.pin is not None:
                    ref = args.pin
                    action_name = "pin"
                elif args.unpin is not None:
                    ref = args.unpin
                    action_name = "unpin"
                elif args.delete is not None:
                    ref = args.delete
                    action_name = "delete"
                else:
                    assert args.edit is not None
                    ref = args.edit
                    action_name = "edit"

                message_id = _resolve_message_ref(ref, target_name, log)
                if message_id is None:
                    all_ok = False
                    continue

                if args.dry_run:
                    log.info(
                        "[dry-run] Would %s message %d in %s (%s)",
                        action_name, message_id, target_name, chat_id,
                    )
                    continue

                try:
                    if args.pin is not None:
                        await client.pin_message(chat_id, message_id)
                        log.info("Pinned message %d in %s", message_id, target_name)
                    elif args.unpin is not None:
                        await client.unpin_message(chat_id, message_id)
                        log.info("Unpinned message %d in %s", message_id, target_name)
                    elif args.delete is not None:
                        await client.delete_message(chat_id, message_id)
                        log.info("Deleted message %d in %s", message_id, target_name)
                    elif args.edit is not None:
                        try:
                            text = prepare_text(args.message_file)
                        except MessageError as e:
                            log.error("%s", e)
                            all_ok = False
                            continue
                        try:
                            await client.edit_message_text(chat_id, message_id, text)
                        except TelegramError as e:
                            if "no text in the message" in e.description.lower():
                                await client.edit_message_caption(chat_id, message_id, text)
                            else:
                                raise
                        log.info("Edited message %d in %s", message_id, target_name)
                except TelegramError as e:
                    log.error("Failed to %s in %s: %s", action_name, target_name, e)
                    await _notify_admin(
                        config,
                        f"penpen ошибка {action_name} в {target_name}: {e}",
                    )
                    all_ok = False

        return 0 if all_ok else 1

    # Resolve reply-to message_id if specified
    reply_to_message_id: int | None = None
    if args.reply_to is not None:
        # Use first target for load_last_id (same ref applies to all targets)
        first_target = args.targets[0] if args.targets else ""
        reply_to_message_id = _resolve_message_ref(args.reply_to, first_target, log)
        if reply_to_message_id is None:
            return 1

    # Optional: download video
    if args.video_url:
        from bot.video_downloader import DownloadError, download, is_youtube_url
        if not is_youtube_url(args.video_url):
            log.error("Not a valid YouTube URL: %s", args.video_url)
            return 1
        log.info("Downloading video: %s", args.video_url)
        try:
            video_path = download(args.video_url, args.media_dir)
            log.info("Downloaded: %s", video_path)
        except DownloadError as e:
            log.error("Download failed: %s", e)
            return 1

    # Scan media
    plan = scan(args.media_dir)
    log.debug("MediaPlan: kind=%s, images=%d, videos=%d, thumbnail=%s",
              plan.kind.name, len(plan.images), len(plan.videos), plan.thumbnail)

    # Prepare text
    try:
        if plan.kind == MediaKind.TEXT_ONLY:
            text = prepare_text(args.message_file)
        else:
            text = prepare_caption(args.message_file)
    except MessageError as e:
        log.error("%s", e)
        await _notify_admin(config, f"penpen ошибка: {e}")
        return 1
    except (CaptionTooLongError, TextTooLongError) as e:
        overflow = e.converted[MAX_CAPTION_LENGTH if isinstance(e, CaptionTooLongError) else 4096:]
        log.error("%s", e)
        targets_str = ", ".join(name for name, _ in targets)
        await _notify_admin(
            config,
            f"penpen сообщение слишком длинное для {targets_str} ({e.length} символов)."
            f" Не отправлено. Остаток:\n\n```\n{overflow}\n```",
            parse_mode="Markdown",
        )
        return 1

    # Dry run summary
    if args.dry_run:
        print(f"[dry-run] Targets: {[name for name, _ in targets]}")
        print(f"[dry-run] Media kind: {plan.kind.name}")
        print(f"[dry-run] Text length: {len(text)} chars")
        print(f"[dry-run] Text preview:\n{text[:200]}{'...' if len(text) > 200 else ''}")
        if reply_to_message_id:
            print(f"[dry-run] Reply to message_id: {reply_to_message_id}")
        for name, chat_id in targets:
            await _send_to_target(
                None, name, chat_id, plan, text,
                dry_run=True, reply_to_message_id=reply_to_message_id,
            )
        return 0

    # Send to all targets in parallel
    async with TelegramClient(config.bot_token) as client:
        tasks = [
            _send_to_target(
                client, name, chat_id, plan, text,
                reply_to_message_id=reply_to_message_id,
            )
            for name, chat_id in targets
        ]
        results: list[Any] = await asyncio.gather(*tasks, return_exceptions=True)

    send_results: list[SendResult] = []
    for r in results:
        if isinstance(r, Exception):
            log.error("Unexpected exception: %s", r)
            send_results.append(
                SendResult(target_name="unknown", chat_id="", success=False, error=str(r))
            )
        elif isinstance(r, SendResult):
            send_results.append(r)

    all_ok = all(r.success for r in send_results)

    # Save last message_id for each target
    for r in send_results:
        if r.success and r.message_id is not None:
            save_last_id(r.target_name, r.message_id)

    # Notify admin about failures
    for r in send_results:
        if not r.success:
            await _notify_admin(
                config,
                f"penpen ошибка отправки в {r.target_name}: {r.error}",
            )

    # Cleanup media if all succeeded
    if all_ok and not args.keep_media:
        deleted = clear(args.media_dir)
        if deleted:
            log.info("Cleaned up %d media file(s)", deleted)

    # Report
    for r in send_results:
        if r.success:
            log.info("✓ %s", r.target_name)
        else:
            log.error("✗ %s: %s", r.target_name, r.error)

    return 0 if all_ok else 1


def main() -> None:
    """CLI entry point."""
    parser = _build_parser()
    ns = parser.parse_args()

    if ns.command == "send":
        args = SendArgs(
            targets=ns.targets,
            video_url=ns.video_url,
            dry_run=ns.dry_run,
            debug=ns.debug,
            message_file=ns.message_file,
            media_dir=ns.media_dir,
            keep_media=ns.keep_media,
            pin=ns.pin,
            unpin=ns.unpin,
            delete=ns.delete,
            edit=ns.edit,
            reply_to=ns.reply_to,
            forward=ns.forward,
        )

        try:
            config = load_config()
        except ConfigError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            sys.exit(1)

        _setup_logging(args.debug, config.log_level)

        exit_code = asyncio.run(_run_send(args, config))
        sys.exit(exit_code)
