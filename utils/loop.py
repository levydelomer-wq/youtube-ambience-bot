import subprocess
import tempfile
import os
import math
from typing import TextIO


def get_video_duration(path: str) -> float:
    """Returns duration in seconds.

    Args:
        path: Path to the video file.

    Returns:
        Duration of the video in seconds.

    Raises:
        RuntimeError: If ffprobe command fails.
        ValueError: If ffprobe returns empty or invalid output.
    """
    cmd: list[str] = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ]
    result: subprocess.CompletedProcess[str] = subprocess.run(
        cmd, capture_output=True, text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {result.stderr}")

    output: str = result.stdout.strip()
    if not output:
        raise ValueError(f"ffprobe returned empty output for {path}")

    try:
        return float(output)
    except ValueError:
        raise ValueError(f"ffprobe returned invalid duration '{output}' for {path}")


def loop_video(input_path: str, output_path: str, duration_hours: int) -> str:
    """Loop a video to reach a target duration.

    Args:
        input_path: Path to the source video.
        output_path: Path for the output video.
        duration_hours: Target duration in hours.

    Returns:
        Path to the output video.
    """
    target_seconds: int = duration_hours * 3600
    base_duration: float = get_video_duration(input_path)

    loops_needed: int = math.ceil(target_seconds / base_duration)

    # Create concat file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        for _ in range(loops_needed):
            f.write(f"file '{os.path.abspath(input_path)}'\n")
        concat_file: str = f.name

    try:
        cmd: list[str] = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-t", str(target_seconds),
            "-c", "copy",
            output_path
        ]

        subprocess.run(cmd, check=True)
        return output_path

    finally:
        os.remove(concat_file)
