"""Media directory scanner for penpen bot."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp"})
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".avi", ".mkv", ".webm"})
THUMBNAIL_NAMES = frozenset({"cover.jpg", "thumbnail.jpg"})


class MediaKind(Enum):
    TEXT_ONLY = auto()
    SINGLE_PHOTO = auto()
    PHOTO_GROUP = auto()
    SINGLE_VIDEO = auto()


@dataclass(frozen=True)
class MediaPlan:
    kind: MediaKind
    images: list[Path] = field(default_factory=list)
    videos: list[Path] = field(default_factory=list)
    thumbnail: Path | None = None


def scan(media_dir: Path) -> MediaPlan:
    """Scan media directory and classify its contents into a MediaPlan.

    Rules:
    - Empty dir → TEXT_ONLY
    - 1 image → SINGLE_PHOTO
    - 2-10 images → PHOTO_GROUP
    - 1 video → SINGLE_VIDEO
    - cover.jpg or thumbnail.jpg → used as video thumbnail, not counted as image
    - Zero-size files are ignored
    """
    if not media_dir.exists():
        return MediaPlan(kind=MediaKind.TEXT_ONLY)

    thumbnail: Path | None = None
    images: list[Path] = []
    videos: list[Path] = []

    for entry in sorted(media_dir.iterdir()):
        if not entry.is_file():
            continue
        if entry.stat().st_size == 0:
            continue

        suffix = entry.suffix.lower()
        name = entry.name.lower()

        if name in THUMBNAIL_NAMES:
            thumbnail = entry
            continue

        if suffix in IMAGE_EXTENSIONS:
            images.append(entry)
        elif suffix in VIDEO_EXTENSIONS:
            videos.append(entry)

    if videos:
        return MediaPlan(kind=MediaKind.SINGLE_VIDEO, videos=videos[:1], thumbnail=thumbnail)

    if len(images) == 0:
        return MediaPlan(kind=MediaKind.TEXT_ONLY)
    elif len(images) == 1:
        return MediaPlan(kind=MediaKind.SINGLE_PHOTO, images=images)
    else:
        return MediaPlan(kind=MediaKind.PHOTO_GROUP, images=images[:10])


def clear(media_dir: Path) -> int:
    """Delete all files in media_dir except .gitkeep. Returns count of deleted files."""
    if not media_dir.exists():
        return 0

    deleted = 0
    for entry in media_dir.iterdir():
        if entry.is_file() and entry.name != ".gitkeep":
            try:
                entry.unlink()
                deleted += 1
            except FileNotFoundError:
                pass
    return deleted
