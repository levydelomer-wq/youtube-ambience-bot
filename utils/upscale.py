from pathlib import Path
import subprocess

def upscale_to_4k(input_video: Path, output_video: Path):
    cmd = [
        "realesrgan-ncnn-vulkan",
        "-i", str(input_video),
        "-o", str(output_video),
        "-n", "realesrgan-x4plus",
        "-s", "2",
        "-f", "mp4",
    ]
    subprocess.run(cmd, check=True)

def frame_video(input_video: Path):
    frames_dir = Path("frames")
    frames_dir.mkdir()
    cmd = [
        "ffmpeg",
        "-i", str(input_video),
        str(frames_dir / "frame_%06d.jpg")
    ]
    subprocess.run(cmd, check=True)

def upscale_frames(input_video: Path):
    frames_dir = Path("frames")
    frames_dir.mkdir()
    cmd = [
        "ffmpeg",
        "-i", str(input_video),
        str(frames_dir / "frame_%06d.jpg")
    ]
    subprocess.run(cmd, check=True)

def clean_frames_dir():
    frames_dir = Path("frames")
    frames_dir.rmdir()
    frames_upscaled_dir = Path("frames_upscaled")
    frames_upscaled_dir.rmdir()