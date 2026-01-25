import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from utils.upscale import (
    frame_video,
    frames_to_video,
    get_video_fps,
    upscale_frames,
    upscale_to_4k,
)


# ============================================================================
# Integration Test Helpers
# ============================================================================


def get_video_resolution(video_path: Path) -> tuple[int, int]:
    """Get the width and height of a video file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    width, height = map(int, result.stdout.strip().split(","))
    return width, height


def get_image_resolution(image_path: Path) -> tuple[int, int]:
    """Get the width and height of an image file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        str(image_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    width, height = map(int, result.stdout.strip().split(","))
    return width, height


def is_valid_image(image_path: Path) -> bool:
    """Check if a file is a valid image using ffprobe."""
    cmd = ["ffprobe", "-v", "error", str(image_path)]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0


def count_frames_in_dir(frames_dir: Path, pattern: str = "frame_*.jpg") -> int:
    """Count the number of frame files in a directory."""
    return len(list(frames_dir.glob(pattern)))


# Skip markers for integration tests
requires_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None,
    reason="ffmpeg not installed"
)
requires_realesrgan = pytest.mark.skipif(
    shutil.which("realesrgan-ncnn-vulkan") is None,
    reason="realesrgan-ncnn-vulkan not installed"
)


@pytest.fixture
def tiny_video(tmp_path: Path) -> Path:
    """Generate a minimal 32x32 test video (0.5s @ 10fps = 5 frames)."""
    video_path = tmp_path / "test_input.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "color=c=red:s=32x32:d=0.5:r=10",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(video_path)
    ], check=True, capture_output=True)
    return video_path


@pytest.fixture
def tiny_frames(tmp_path: Path) -> Path:
    """Generate a set of 32x32 test frames for upscaling tests."""
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    for i in range(1, 6):
        frame_path = frames_dir / f"frame_{i:06d}.jpg"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "color=c=blue:s=32x32",
            "-frames:v", "1",
            str(frame_path)
        ], check=True, capture_output=True)
    return frames_dir


# ============================================================================
# Unit Tests (Mocked)
# ============================================================================


class TestGetVideoFps:
    """Tests for get_video_fps function."""

    def test_standard_framerate(self) -> None:
        """Test parsing a standard 30fps video."""
        mock_output = json.dumps({
            "streams": [
                {"codec_type": "video", "r_frame_rate": "30/1"}
            ]
        })

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output)
            fps = get_video_fps(Path("/test/video.mp4"))

        assert fps == 30.0
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "ffprobe" in args
        assert "/test/video.mp4" in args

    def test_fractional_framerate(self) -> None:
        """Test parsing NTSC 23.976fps (24000/1001)."""
        mock_output = json.dumps({
            "streams": [
                {"codec_type": "video", "r_frame_rate": "24000/1001"}
            ]
        })

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output)
            fps = get_video_fps(Path("/test/video.mp4"))

        assert abs(fps - 23.976) < 0.01

    def test_no_video_stream_returns_default(self) -> None:
        """Test default 30fps when no video stream found."""
        mock_output = json.dumps({
            "streams": [
                {"codec_type": "audio", "sample_rate": "48000"}
            ]
        })

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output)
            fps = get_video_fps(Path("/test/audio.mp4"))

        assert fps == 30.0

    def test_empty_streams_returns_default(self) -> None:
        """Test default 30fps when streams array is empty."""
        mock_output = json.dumps({"streams": []})

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output)
            fps = get_video_fps(Path("/test/empty.mp4"))

        assert fps == 30.0


class TestFrameVideo:
    """Tests for frame_video function."""

    def test_extracts_frames_with_ffmpeg(self, tmp_path: Path) -> None:
        """Test that ffmpeg is called with correct arguments."""
        input_video = Path("/test/input.mp4")
        frames_dir = tmp_path / "frames"

        with patch("subprocess.run") as mock_run:
            frame_video(input_video, frames_dir)

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-i" in args
        assert str(input_video) in args
        assert "frame_%06d.jpg" in args[-1]

    def test_creates_frames_directory(self, tmp_path: Path) -> None:
        """Test that frames directory is created."""
        frames_dir = tmp_path / "new_frames"

        with patch("subprocess.run"):
            frame_video(Path("/test/input.mp4"), frames_dir)

        assert frames_dir.exists()

    def test_default_frames_directory(self) -> None:
        """Test that default 'frames' directory is used when not specified."""
        with patch("subprocess.run") as mock_run:
            with patch.object(Path, "mkdir"):
                frame_video(Path("/test/input.mp4"))

        args = mock_run.call_args[0][0]
        assert "frames" in args[-1]


class TestUpscaleFrames:
    """Tests for upscale_frames function."""

    def test_calls_realesrgan_with_correct_args(self, tmp_path: Path) -> None:
        """Test that realesrgan is called with correct model and scale."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            upscale_frames(input_dir, output_dir)

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "realesrgan-ncnn-vulkan"
        assert "-i" in args
        assert str(input_dir) in args
        assert "-o" in args
        assert str(output_dir) in args
        assert "-n" in args
        assert "realesrgan-x4plus" in args
        assert "-s" in args
        assert "2" in args
        assert "-f" in args
        assert "jpg" in args

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Test that output directory is created."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        with patch("subprocess.run"):
            upscale_frames(input_dir, output_dir)

        assert output_dir.exists()


class TestFramesToVideo:
    """Tests for frames_to_video function."""

    def test_calls_ffmpeg_with_correct_args(self, tmp_path: Path) -> None:
        """Test that ffmpeg is called with correct encoding settings."""
        frames_dir = tmp_path / "frames"
        output_video = tmp_path / "output.mp4"
        frames_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            frames_to_video(frames_dir, output_video, fps=24.0)

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-y" in args  # Overwrite
        assert "-framerate" in args
        assert "24.0" in args
        assert "-c:v" in args
        assert "libx264" in args
        assert "-pix_fmt" in args
        assert "yuv420p" in args
        assert "-crf" in args
        assert "18" in args
        assert str(output_video) in args


class TestUpscaleTo4k:
    """Tests for upscale_to_4k orchestration function."""

    def test_pipeline_executes_in_order(self, tmp_path: Path) -> None:
        """Test that the full pipeline executes in correct order."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        input_video.touch()

        with patch("utils.upscale.get_video_fps", return_value=30.0) as mock_fps, \
             patch("utils.upscale.frame_video") as mock_frame, \
             patch("utils.upscale.upscale_frames") as mock_upscale, \
             patch("utils.upscale.frames_to_video") as mock_reassemble:

            upscale_to_4k(input_video, output_video)

            # Verify all functions were called
            mock_fps.assert_called_once_with(input_video)
            mock_frame.assert_called_once()
            mock_upscale.assert_called_once()
            mock_reassemble.assert_called_once()

            # Verify frames_to_video received correct fps
            reassemble_call = mock_reassemble.call_args
            assert reassemble_call[0][2] == 30.0  # fps argument

    def test_uses_temp_directory(self, tmp_path: Path) -> None:
        """Test that temporary directory is used for intermediate files."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        input_video.touch()

        with patch("utils.upscale.get_video_fps", return_value=30.0), \
             patch("utils.upscale.frame_video") as mock_frame, \
             patch("utils.upscale.upscale_frames") as mock_upscale, \
             patch("utils.upscale.frames_to_video"):

            upscale_to_4k(input_video, output_video)

            # Check that frame_video was called with a temp directory path
            frames_dir = mock_frame.call_args[0][1]
            assert "tmp" in str(frames_dir).lower() or "/var" in str(frames_dir)

            # Check that upscale_frames input matches frame_video output
            upscale_input = mock_upscale.call_args[0][0]
            assert upscale_input == frames_dir

    def test_preserves_original_framerate(self, tmp_path: Path) -> None:
        """Test that original video framerate is preserved in output."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        input_video.touch()

        with patch("utils.upscale.get_video_fps", return_value=23.976) as mock_fps, \
             patch("utils.upscale.frame_video"), \
             patch("utils.upscale.upscale_frames"), \
             patch("utils.upscale.frames_to_video") as mock_reassemble:

            upscale_to_4k(input_video, output_video)

            # Verify fps was extracted from input
            mock_fps.assert_called_once_with(input_video)

            # Verify same fps passed to output
            reassemble_call = mock_reassemble.call_args
            assert reassemble_call[0][2] == 23.976


# ============================================================================
# Integration Tests (Real Execution)
# ============================================================================


@requires_ffmpeg
class TestGetVideoFpsIntegration:
    """Integration tests for get_video_fps with real video files."""

    def test_extracts_fps_from_real_video(self, tiny_video: Path) -> None:
        """Test FPS extraction on actual video file."""
        fps = get_video_fps(tiny_video)
        assert fps == 10.0

    def test_extracts_fractional_fps(self, tmp_path: Path) -> None:
        """Test extraction of NTSC 23.976fps from real video."""
        video_path = tmp_path / "ntsc.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "color=c=green:s=16x16:d=0.1:r=24000/1001",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(video_path)
        ], check=True, capture_output=True)

        fps = get_video_fps(video_path)
        assert abs(fps - 23.976) < 0.01


@requires_ffmpeg
class TestFrameVideoIntegration:
    """Integration tests for frame extraction with real videos."""

    def test_extracts_correct_number_of_frames(
        self, tiny_video: Path, tmp_path: Path
    ) -> None:
        """Test that correct number of frames are extracted."""
        frames_dir = tmp_path / "extracted_frames"

        frame_video(tiny_video, frames_dir)

        frame_count = count_frames_in_dir(frames_dir)
        assert frame_count == 5  # 0.5s @ 10fps

    def test_extracted_frames_are_valid_images(
        self, tiny_video: Path, tmp_path: Path
    ) -> None:
        """Test that extracted frames are valid image files."""
        frames_dir = tmp_path / "extracted_frames"

        frame_video(tiny_video, frames_dir)

        for frame in frames_dir.glob("frame_*.jpg"):
            assert is_valid_image(frame), f"{frame} is not a valid image"

    def test_extracted_frames_have_correct_resolution(
        self, tiny_video: Path, tmp_path: Path
    ) -> None:
        """Test that frames have same resolution as source video."""
        frames_dir = tmp_path / "extracted_frames"

        frame_video(tiny_video, frames_dir)

        first_frame = frames_dir / "frame_000001.jpg"
        width, height = get_image_resolution(first_frame)
        assert width == 32
        assert height == 32


@requires_ffmpeg
class TestFramesToVideoIntegration:
    """Integration tests for video reassembly from frames."""

    def test_creates_valid_video_from_frames(
        self, tiny_frames: Path, tmp_path: Path
    ) -> None:
        """Test that frames are reassembled into a valid video."""
        output_video = tmp_path / "output.mp4"

        frames_to_video(tiny_frames, output_video, fps=10.0)

        assert output_video.exists()
        width, height = get_video_resolution(output_video)
        assert width == 32
        assert height == 32

    def test_output_video_has_correct_fps(
        self, tiny_frames: Path, tmp_path: Path
    ) -> None:
        """Test that output video has the specified framerate."""
        output_video = tmp_path / "output.mp4"

        frames_to_video(tiny_frames, output_video, fps=24.0)

        fps = get_video_fps(output_video)
        assert fps == 24.0


@requires_ffmpeg
@requires_realesrgan
class TestUpscaleFramesIntegration:
    """Integration tests for frame upscaling with RealESRGAN."""

    def test_upscales_frames_to_higher_resolution(
        self, tiny_frames: Path, tmp_path: Path
    ) -> None:
        """Test that frames are upscaled to higher resolution."""
        output_dir = tmp_path / "upscaled"

        upscale_frames(tiny_frames, output_dir)

        # Check output frames exist
        output_count = count_frames_in_dir(output_dir)
        assert output_count == 5

        # Check resolution increased (32x32 -> 64x64 with -s 2)
        first_output = output_dir / "frame_000001.jpg"
        width, height = get_image_resolution(first_output)
        assert width == 64, f"Expected width 64, got {width}"
        assert height == 64, f"Expected height 64, got {height}"

    def test_upscaled_frames_are_valid_images(
        self, tiny_frames: Path, tmp_path: Path
    ) -> None:
        """Test that upscaled frames are valid image files."""
        output_dir = tmp_path / "upscaled"

        upscale_frames(tiny_frames, output_dir)

        for frame in output_dir.glob("frame_*.jpg"):
            assert is_valid_image(frame), f"{frame} is not a valid image"


@requires_ffmpeg
@requires_realesrgan
class TestUpscaleTo4kIntegration:
    """Integration tests for the full upscaling pipeline."""

    def test_full_pipeline_produces_upscaled_video(
        self, tiny_video: Path, tmp_path: Path
    ) -> None:
        """Test complete pipeline: 32x32 input -> 64x64 output."""
        output_video = tmp_path / "upscaled_output.mp4"

        upscale_to_4k(tiny_video, output_video)

        assert output_video.exists()

        # Verify output resolution is larger than input
        input_w, input_h = get_video_resolution(tiny_video)
        output_w, output_h = get_video_resolution(output_video)

        assert output_w > input_w, f"Output width {output_w} not > input {input_w}"
        assert output_h > input_h, f"Output height {output_h} not > input {input_h}"

    def test_full_pipeline_preserves_framerate(
        self, tiny_video: Path, tmp_path: Path
    ) -> None:
        """Test that framerate is preserved through the pipeline."""
        output_video = tmp_path / "upscaled_output.mp4"

        upscale_to_4k(tiny_video, output_video)

        input_fps = get_video_fps(tiny_video)
        output_fps = get_video_fps(output_video)

        assert output_fps == input_fps, f"FPS changed: {input_fps} -> {output_fps}"

    def test_output_video_is_playable(
        self, tiny_video: Path, tmp_path: Path
    ) -> None:
        """Test that output video can be probed successfully."""
        output_video = tmp_path / "upscaled_output.mp4"

        upscale_to_4k(tiny_video, output_video)

        # ffprobe should succeed on valid video
        result = subprocess.run(
            ["ffprobe", "-v", "error", str(output_video)],
            capture_output=True
        )
        assert result.returncode == 0, f"ffprobe failed: {result.stderr.decode()}"
