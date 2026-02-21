"""Tests for bot/video_downloader.py."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from bot.video_downloader import DownloadError, download, is_youtube_url


class TestIsYoutubeUrl:
    def test_valid_watch_url(self) -> None:
        assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_valid_short_url(self) -> None:
        assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ")

    def test_valid_shorts_url(self) -> None:
        assert is_youtube_url("https://www.youtube.com/shorts/abc123")

    def test_valid_embed_url(self) -> None:
        assert is_youtube_url("https://www.youtube.com/embed/abc123")

    def test_invalid_random_url(self) -> None:
        assert not is_youtube_url("https://example.com/video")

    def test_invalid_vimeo_url(self) -> None:
        assert not is_youtube_url("https://vimeo.com/123456")

    def test_invalid_empty_string(self) -> None:
        assert not is_youtube_url("")

    def test_valid_no_www(self) -> None:
        assert is_youtube_url("https://youtube.com/watch?v=abc")


class TestDownload:
    def test_injection_chars_raise_download_error(self, tmp_path: Path) -> None:
        with pytest.raises(DownloadError, match="dangerous"):
            download("https://youtube.com/watch?v=abc; rm -rf /", tmp_path)

    def test_pipe_char_raises_download_error(self, tmp_path: Path) -> None:
        with pytest.raises(DownloadError, match="dangerous"):
            download("https://youtube.com/watch?v=abc|evil", tmp_path)

    def test_ampersand_raises_download_error(self, tmp_path: Path) -> None:
        with pytest.raises(DownloadError, match="dangerous"):
            download("https://youtube.com/watch?v=abc&other=bad", tmp_path)

    def test_yt_dlp_not_found_raises_download_error(self, tmp_path: Path) -> None:
        with (
            patch("shutil.which", return_value=None),
            pytest.raises(DownloadError, match="yt-dlp not found"),
        ):
            download("https://youtube.com/watch?v=abc", tmp_path)

    def test_successful_download_returns_mp4_path(self, tmp_path: Path) -> None:
        media_dir = tmp_path / "media"
        media_dir.mkdir()

        # Create a fake mp4 file that yt-dlp would have created
        fake_mp4 = media_dir / "My Video.mp4"
        fake_mp4.write_bytes(b"fake mp4 data")

        fake_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        with (
            patch("shutil.which", return_value="/usr/bin/yt-dlp"),
            patch("subprocess.run", return_value=fake_result),
        ):
            result = download("https://youtube.com/watch?v=abc", media_dir)

        assert result == fake_mp4

    def test_yt_dlp_failure_raises_download_error(self, tmp_path: Path) -> None:
        fake_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="Error: video unavailable"
        )

        with (
            patch("shutil.which", return_value="/usr/bin/yt-dlp"),
            patch("subprocess.run", return_value=fake_result),
            pytest.raises(DownloadError, match="exited with code 1"),
        ):
            download("https://youtube.com/watch?v=abc", tmp_path)
