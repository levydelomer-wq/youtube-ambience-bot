from pathlib import Path
import subprocess
import shutil


def upscale_to_4k(input_video: Path, output_video: Path) -> None:
    """Upscale a video to 4K using RealESRGAN.

    Args:
        input_video: Path to the input video.
        output_video: Path for the upscaled output video.
    """
    cmd: list[str] = [
        "realesrgan-ncnn-vulkan",
        "-i", str(input_video),
        "-o", str(output_video),
        "-n", "realesrgan-x4plus",
        "-s", "2",
        "-f", "mp4",
    ]
    subprocess.run(cmd, check=True)


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
    ]
    subprocess.run(cmd, check=True)


def clean_frames_dir() -> None:
    """Clean up frame directories."""
    frames_dir: Path = Path("frames")
    frames_upscaled_dir: Path = Path("frames_upscaled")

    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    if frames_upscaled_dir.exists():
        shutil.rmtree(frames_upscaled_dir)
