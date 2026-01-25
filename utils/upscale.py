import json
import subprocess
import tempfile
from pathlib import Path


def get_video_fps(video_path: Path) -> float:
    """Get the framerate of a video file.

    Args:
        video_path: Path to the video file.

    Returns:
        Frames per second as a float.
    """
    cmd: list[str] = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            # Parse framerate like "30/1" or "24000/1001"
            r_frame_rate: str = stream.get("r_frame_rate", "30/1")
            num, denom = map(int, r_frame_rate.split("/"))
            return num / denom

    return 30.0  # Default fallback


def frames_to_video(frames_dir: Path, output_video: Path, fps: float) -> None:
    """Reassemble frames into a video file.

    Args:
        frames_dir: Directory containing the upscaled frames.
        output_video: Path for the output video.
        fps: Framerate for the output video.
    """
    cmd: list[str] = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%06d.jpg"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",  # High quality
        str(output_video)
    ]
    subprocess.run(cmd, check=True)


def upscale_to_4k(input_video: Path, output_video: Path) -> None:
    """Upscale a video to 4K using RealESRGAN.

    This extracts frames, upscales each frame with RealESRGAN,
    and reassembles them into a video.

    Args:
        input_video: Path to the input video.
        output_video: Path for the upscaled output video.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        frames_dir = tmp_path / "frames"
        upscaled_dir = tmp_path / "upscaled"

        # Get original framerate
        fps = get_video_fps(input_video)

        # Extract frames
        frame_video(input_video, frames_dir)

        # Upscale frames
        upscale_frames(frames_dir, upscaled_dir)

        # Reassemble into video
        frames_to_video(upscaled_dir, output_video, fps)


def frame_video(input_video: Path, frames_dir: Path | None = None) -> None:
    """Extract frames from a video file.

    Args:
        input_video: Path to the video file.
        frames_dir: Directory to save frames. Defaults to "frames".
    """
    if frames_dir is None:
        frames_dir = Path("frames")
    frames_dir.mkdir(exist_ok=True)
    cmd: list[str] = [
        "ffmpeg",
        "-i", str(input_video),
        str(frames_dir / "frame_%06d.jpg")
    ]
    subprocess.run(cmd, check=True)


def upscale_frames(input_dir: Path, output_dir: Path) -> None:
    """Upscale extracted frames using RealESRGAN.

    Args:
        input_dir: Directory containing input frames.
        output_dir: Directory for upscaled frames.
    """
    output_dir.mkdir(exist_ok=True)
    cmd: list[str] = [
        "realesrgan-ncnn-vulkan",
        "-i", str(input_dir),
        "-o", str(output_dir),
        "-n", "realesrgan-x4plus",
        "-s", "2",
        "-f", "jpg",  # Output JPG to match frames_to_video expectation
    ]
    subprocess.run(cmd, check=True)
