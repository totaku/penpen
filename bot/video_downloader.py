"""YouTube video downloader using yt-dlp subprocess."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

YOUTUBE_URL_RE = re.compile(
    r"^https?://(www\.)?(youtube\.com/(watch\?.*v=|shorts/|embed/)|youtu\.be/)"
)
INJECTION_CHARS = frozenset(";|&`$(){}[]<>\\")

# cookies.txt лежит в корне проекта рядом с pyproject.toml
_PROJECT_ROOT = Path(__file__).parent.parent
COOKIES_FILE = _PROJECT_ROOT / "cookies.txt"


class DownloadError(Exception):
    """Raised when video download fails."""


def is_youtube_url(url: str) -> bool:
    """Return True if the URL looks like a valid YouTube URL."""
    return bool(YOUTUBE_URL_RE.match(url))


def _check_for_injection(url: str) -> None:
    """Raise DownloadError if URL contains shell injection characters."""
    found = [c for c in url if c in INJECTION_CHARS]
    if found:
        raise DownloadError(
            f"URL contains potentially dangerous characters: {found!r}"
        )


def download(url: str, media_dir: Path) -> Path:
    """Download a YouTube video to media_dir using yt-dlp.

    Returns the path to the downloaded .mp4 file.
    Also downloads thumbnail as cover.jpg if available.

    Raises DownloadError on any failure.
    """
    _check_for_injection(url)

    yt_dlp_path = shutil.which("yt-dlp")
    if yt_dlp_path is None:
        raise DownloadError(
            "yt-dlp not found. Install it with: pip install yt-dlp"
        )

    media_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(media_dir / "%(title)s.%(ext)s")

    cmd = [
        yt_dlp_path,
        # H.264 + m4a — гарантированная совместимость с Mac/iOS/Telegram
        "--format", (
            "bestvideo[height<=720][vcodec^=avc]+bestaudio[ext=m4a]"
            "/bestvideo[height<=720][ext=mp4]+bestaudio"
            "/best[height<=720]"
        ),
        "--merge-output-format", "mp4",
        # Принудительно перекодируем в H.264 MP4 (AV1 и другие не воспроизводятся на Mac)
        "--recode-video", "mp4",
        # moov atom в начало — обязательно для streaming в Telegram
        "--postprocessor-args", "ffmpeg:-movflags +faststart",
        "--remote-components", "ejs:github",
        "--write-thumbnail",
        "--convert-thumbnails", "jpg",
        "--output", output_template,
        "--no-playlist",
    ]

    if COOKIES_FILE.exists():
        cmd += ["--cookies", str(COOKIES_FILE)]

    cmd.append(url)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as e:
        raise DownloadError(f"yt-dlp executable not found: {e}") from e
    except OSError as e:
        raise DownloadError(f"Failed to run yt-dlp: {e}") from e

    if result.returncode != 0:
        # If cookies file is stale, retry with cookies from browser
        if COOKIES_FILE.exists() and "cookies are no longer valid" in result.stderr:
            cmd_retry = [a for a in cmd if a != str(COOKIES_FILE) and a != "--cookies"]
            cmd_retry += ["--cookies-from-browser", "chrome"]
            try:
                result = subprocess.run(
                    cmd_retry, capture_output=True, text=True, check=False,
                )
            except OSError as e:
                raise DownloadError(f"Failed to run yt-dlp: {e}") from e
        if result.returncode != 0:
            raise DownloadError(
                f"yt-dlp exited with code {result.returncode}:\n{result.stderr}"
            )

    # Find the downloaded mp4 file
    mp4_files = sorted(media_dir.glob("*.mp4"))
    if not mp4_files:
        raise DownloadError(f"yt-dlp succeeded but no .mp4 file found in {media_dir}")

    # Rename the thumbnail to cover.jpg if it exists
    jpg_files = [
        f for f in media_dir.iterdir()
        if f.suffix.lower() == ".jpg" and f.name != "cover.jpg"
    ]
    if jpg_files:
        cover_path = media_dir / "cover.jpg"
        jpg_files[0].rename(cover_path)

    return mp4_files[-1]
