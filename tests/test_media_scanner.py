"""Tests for bot/media_scanner.py."""

from __future__ import annotations

from pathlib import Path

from bot.media_scanner import MediaKind, clear, scan


def _make_file(media: Path, name: str, size: int = 100) -> Path:
    p = media / name
    p.write_bytes(b"x" * size)
    return p


class TestScan:
    def test_empty_dir_is_text_only(self, tmp_media: Path) -> None:
        plan = scan(tmp_media)
        assert plan.kind == MediaKind.TEXT_ONLY

    def test_single_image_is_single_photo(self, tmp_media: Path) -> None:
        _make_file(tmp_media, "photo.jpg")
        plan = scan(tmp_media)
        assert plan.kind == MediaKind.SINGLE_PHOTO
        assert len(plan.images) == 1

    def test_three_images_are_photo_group(self, tmp_media: Path) -> None:
        for i in range(3):
            _make_file(tmp_media, f"photo_{i}.jpg")
        plan = scan(tmp_media)
        assert plan.kind == MediaKind.PHOTO_GROUP
        assert len(plan.images) == 3

    def test_single_video_is_single_video(self, tmp_media: Path) -> None:
        _make_file(tmp_media, "clip.mp4")
        plan = scan(tmp_media)
        assert plan.kind == MediaKind.SINGLE_VIDEO
        assert len(plan.videos) == 1

    def test_image_alongside_video_becomes_thumbnail(self, tmp_media: Path) -> None:
        _make_file(tmp_media, "video.mp4")
        _make_file(tmp_media, "cover.jpg")
        plan = scan(tmp_media)
        assert plan.kind == MediaKind.SINGLE_VIDEO
        assert plan.thumbnail is not None
        assert plan.thumbnail.name == "cover.jpg"

    def test_video_without_image_has_no_thumbnail(self, tmp_media: Path) -> None:
        _make_file(tmp_media, "video.mp4")
        plan = scan(tmp_media)
        assert plan.kind == MediaKind.SINGLE_VIDEO
        assert plan.thumbnail is None

    def test_zero_size_file_ignored(self, tmp_media: Path) -> None:
        _make_file(tmp_media, "photo.jpg", size=0)
        plan = scan(tmp_media)
        assert plan.kind == MediaKind.TEXT_ONLY

    def test_nonexistent_dir_is_text_only(self, tmp_path: Path) -> None:
        plan = scan(tmp_path / "nonexistent")
        assert plan.kind == MediaKind.TEXT_ONLY

    def test_video_takes_priority_over_images(self, tmp_media: Path) -> None:
        _make_file(tmp_media, "photo.jpg")
        _make_file(tmp_media, "video.mp4")
        plan = scan(tmp_media)
        assert plan.kind == MediaKind.SINGLE_VIDEO

    def test_photo_group_capped_at_10(self, tmp_media: Path) -> None:
        for i in range(12):
            _make_file(tmp_media, f"img_{i:02d}.jpg")
        plan = scan(tmp_media)
        assert plan.kind == MediaKind.PHOTO_GROUP
        assert len(plan.images) == 10

    def test_two_images_is_photo_group(self, tmp_media: Path) -> None:
        _make_file(tmp_media, "a.jpg")
        _make_file(tmp_media, "b.jpg")
        plan = scan(tmp_media)
        assert plan.kind == MediaKind.PHOTO_GROUP


class TestClear:
    def test_clear_removes_files_keeps_gitkeep(self, tmp_media: Path) -> None:
        _make_file(tmp_media, "photo.jpg")
        _make_file(tmp_media, "video.mp4")
        deleted = clear(tmp_media)
        assert deleted == 2
        assert (tmp_media / ".gitkeep").exists()
        assert not (tmp_media / "photo.jpg").exists()
        assert not (tmp_media / "video.mp4").exists()

    def test_clear_empty_dir_returns_zero(self, tmp_media: Path) -> None:
        deleted = clear(tmp_media)
        assert deleted == 0

    def test_clear_nonexistent_dir_returns_zero(self, tmp_path: Path) -> None:
        deleted = clear(tmp_path / "nonexistent")
        assert deleted == 0
