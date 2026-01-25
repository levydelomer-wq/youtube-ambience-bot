import subprocess
import tempfile
import os
import math


def get_audio_duration(path: str) -> float:
    """Returns audio duration in seconds.

    Args:
        path: Path to the audio file.

    Returns:
        Duration of the audio in seconds.

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


def loop_audio(
    input_path: str,
    output_path: str,
    target_duration_seconds: float,
    crossfade_seconds: float = 3.0
) -> str:
    """Loop audio to reach a target duration with smooth crossfades.

    Args:
        input_path: Path to the source audio.
        output_path: Path for the output audio.
        target_duration_seconds: Target duration in seconds.
        crossfade_seconds: Duration of crossfade between loops.

    Returns:
        Path to the output audio.
    """
    base_duration: float = get_audio_duration(input_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # For short target durations, just trim
    if target_duration_seconds <= base_duration:
        cmd: list[str] = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-t", str(target_duration_seconds),
            "-c", "copy",
            output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    # Calculate loops needed (accounting for crossfade overlap)
    effective_duration: float = base_duration - crossfade_seconds
    loops_needed: int = math.ceil(target_duration_seconds / effective_duration) + 1

    # Build filter_complex for crossfading multiple inputs
    # Each loop overlaps with the next by crossfade_seconds
    inputs: list[str] = []
    for _ in range(loops_needed):
        inputs.extend(["-i", input_path])

    # Build the acrossfade chain
    filter_parts: list[str] = []
    current_input = "[0:a]"

    for i in range(1, loops_needed):
        next_input = f"[{i}:a]"
        output_label = f"[a{i}]" if i < loops_needed - 1 else "[out]"
        filter_parts.append(
            f"{current_input}{next_input}acrossfade=d={crossfade_seconds}:c1=tri:c2=tri{output_label}"
        )
        current_input = output_label

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-t", str(target_duration_seconds),
        "-c:a", "libmp3lame", "-q:a", "2",
        output_path
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def merge_audio_video(video_path: str, audio_path: str, output_path: str) -> str:
    """Merge audio track into video file.

    The audio will be trimmed or looped to match video duration.

    Args:
        video_path: Path to the video file.
        audio_path: Path to the audio file.
        output_path: Path for the merged output.

    Returns:
        Path to the merged video with audio.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd: list[str] = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path
