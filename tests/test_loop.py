import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from utils.loop import get_video_duration, loop_video


class TestGetVideoDuration:
    """Tests for get_video_duration function."""

    def test_returns_duration_as_float(self) -> None:
        """Test that duration is returned as a float."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="123.456\n",
                stderr=""
            )
            duration = get_video_duration("/test/video.mp4")

        assert duration == 123.456
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "ffprobe" in args
        assert "/test/video.mp4" in args

    def test_strips_whitespace_from_output(self) -> None:
        """Test that whitespace is stripped from ffprobe output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="  60.0  \n\n",
                stderr=""
            )
            duration = get_video_duration("/test/video.mp4")

        assert duration == 60.0

    def test_raises_runtime_error_on_ffprobe_failure(self) -> None:
        """Test that RuntimeError is raised when ffprobe fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="No such file"
            )

            with pytest.raises(RuntimeError, match="ffprobe failed"):
                get_video_duration("/nonexistent/video.mp4")

    def test_raises_value_error_on_empty_output(self) -> None:
        """Test that ValueError is raised when ffprobe returns empty output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr=""
            )

            with pytest.raises(ValueError, match="empty output"):
                get_video_duration("/test/video.mp4")

    def test_raises_value_error_on_invalid_duration(self) -> None:
        """Test that ValueError is raised when duration is not a number."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="not_a_number",
                stderr=""
            )

            with pytest.raises(ValueError, match="invalid duration"):
                get_video_duration("/test/video.mp4")


class TestLoopVideo:
    """Tests for loop_video function."""

    def test_calculates_correct_loop_count(self, tmp_path: Path) -> None:
        """Test that correct number of loops is calculated."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        input_video.touch()

        # 60 second video, 1 hour target = 60 loops needed
        with patch("utils.loop.get_video_duration", return_value=60.0), \
             patch("subprocess.run") as mock_run:

            loop_video(str(input_video), str(output_video), duration_hours=1)

        # Check ffmpeg was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"

    def test_creates_concat_file_with_correct_entries(self, tmp_path: Path) -> None:
        """Test that concat file has correct number of file entries."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        input_video.touch()

        concat_contents: list[str] = []

        original_named_temp = __builtins__["open"] if "open" in dir(__builtins__) else open

        # 30 second video, 1 hour target = 120 loops
        with patch("utils.loop.get_video_duration", return_value=30.0), \
             patch("subprocess.run"), \
             patch("tempfile.NamedTemporaryFile") as mock_temp:

            # Capture what's written to the concat file
            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(return_value=mock_file)
            mock_file.__exit__ = MagicMock(return_value=False)
            mock_file.name = str(tmp_path / "concat.txt")
            mock_temp.return_value = mock_file

            with patch("os.remove"):
                loop_video(str(input_video), str(output_video), duration_hours=1)

            # Count write calls (one per loop)
            write_calls = mock_file.write.call_args_list
            assert len(write_calls) == 120  # ceil(3600 / 30) = 120

    def test_ffmpeg_called_with_correct_duration(self, tmp_path: Path) -> None:
        """Test that ffmpeg is called with target duration."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        input_video.touch()

        with patch("utils.loop.get_video_duration", return_value=60.0), \
             patch("subprocess.run") as mock_run, \
             patch("os.remove"):

            loop_video(str(input_video), str(output_video), duration_hours=2)

        args = mock_run.call_args[0][0]
        # 2 hours = 7200 seconds
        assert "-t" in args
        t_index = args.index("-t")
        assert args[t_index + 1] == "7200"

    def test_cleans_up_concat_file(self, tmp_path: Path) -> None:
        """Test that concat file is removed after processing."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        input_video.touch()

        with patch("utils.loop.get_video_duration", return_value=60.0), \
             patch("subprocess.run"), \
             patch("os.remove") as mock_remove:

            loop_video(str(input_video), str(output_video), duration_hours=1)

        # os.remove should be called to clean up concat file
        mock_remove.assert_called_once()

    def test_cleans_up_concat_file_on_error(self, tmp_path: Path) -> None:
        """Test that concat file is cleaned up even if ffmpeg fails."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        input_video.touch()

        with patch("utils.loop.get_video_duration", return_value=60.0), \
             patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "ffmpeg")), \
             patch("os.remove") as mock_remove:

            with pytest.raises(subprocess.CalledProcessError):
                loop_video(str(input_video), str(output_video), duration_hours=1)

        # Cleanup should still happen
        mock_remove.assert_called_once()

    def test_returns_output_path(self, tmp_path: Path) -> None:
        """Test that output path is returned."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        input_video.touch()

        with patch("utils.loop.get_video_duration", return_value=60.0), \
             patch("subprocess.run"), \
             patch("os.remove"):

            result = loop_video(str(input_video), str(output_video), duration_hours=1)

        assert result == str(output_video)

    def test_uses_stream_copy_for_efficiency(self, tmp_path: Path) -> None:
        """Test that ffmpeg uses stream copy (no re-encoding)."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        input_video.touch()

        with patch("utils.loop.get_video_duration", return_value=60.0), \
             patch("subprocess.run") as mock_run, \
             patch("os.remove"):

            loop_video(str(input_video), str(output_video), duration_hours=1)

        args = mock_run.call_args[0][0]
        assert "-c" in args
        c_index = args.index("-c")
        assert args[c_index + 1] == "copy"
