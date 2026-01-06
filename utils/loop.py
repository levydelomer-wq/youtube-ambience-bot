import subprocess
import tempfile
import os
import math

def get_video_duration(path: str) -> float:
    """Returns duration in seconds"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def loop_video(input_path: str, output_path: str, duration_hours: int):
    target_seconds = duration_hours * 3600
    base_duration = get_video_duration(input_path)

    loops_needed = math.ceil(target_seconds / base_duration)

    # Create concat file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        for _ in range(loops_needed):
            f.write(f"file '{os.path.abspath(input_path)}'\n")
        concat_file = f.name

    try:
        cmd = [
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
