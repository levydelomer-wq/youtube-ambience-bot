import re
import sys

from agents.metadata_agent import MetadataAgent
from agents.prompt_agent import PromptAgent
from agents.image_agent import ImageAgent
from agents.video_agent import VideoAgent
from agents.sound_agent import SoundAgent
from bot_types import Concept, Metadata, Prompts
from config import DRY_RUN
from video_backends.mock import MockVideoBackend
from video_backends.base import VideoBackend
from audio_backends.mock import MockAudioBackend
from audio_backends.base import AudioBackend
from utils.loop import loop_video, get_video_duration
from utils.audio import loop_audio, merge_audio_video
from utils.upload import upload_video
from utils.upscale import upscale_to_4k
from concepts import get_random_concept, get_concept_by_name


def parse_duration_hours(duration_str: str) -> int:
    """Parse duration string like '10 hours' into integer hours."""
    match = re.search(r"(\d+)\s*hour", duration_str.lower())
    if match:
        return int(match.group(1))
    raise ValueError(f"Could not parse duration: {duration_str}")


def slugify(text: str) -> str:
    """Convert text to filename-safe slug."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


# Get concept from CLI arg, or pick random
if len(sys.argv) > 1:
    concept_name = " ".join(sys.argv[1:])
    concept = get_concept_by_name(concept_name)
    if concept is None:
        print(f"Unknown concept: {concept_name}")
        print("Available: cozy fireplace, thunderstorm, rainy window, ocean waves, etc.")
        sys.exit(1)
else:
    concept = get_random_concept()

print(f"Selected concept: {concept['ambience']}")

# Derived values
duration_hours: int = parse_duration_hours(concept["duration"])
slug: str = slugify(concept["ambience"])

# Metadata
print("Generating metadata")
metadata: Metadata = MetadataAgent().generate(concept)
print("Metadata generated")

# Prompts
print("Generating prompts")
prompt_agent: PromptAgent = PromptAgent()
prompts: Prompts = prompt_agent.generate(concept)
print("Prompts generated")

# Image
image_path: str
if DRY_RUN:
    image_path = "assets/mock/mock_image.jpg"
else:
    image_path = ImageAgent().run(
        image_prompt=prompts["image_prompt"],
        filename=f"{slug}_master.png"
    )

# Base video
video_backend: VideoBackend | None = MockVideoBackend() if DRY_RUN else None
video_agent: VideoAgent = VideoAgent(backend=video_backend)
base_video: str = video_agent.run(
    image_path=image_path,
    video_prompt=prompts["video_prompt"],
    filename=f"{slug}_base.mp4"
)

# Audio
print("Generating audio")
audio_backend: AudioBackend | None = MockAudioBackend() if DRY_RUN else None
sound_agent: SoundAgent = SoundAgent(backend=audio_backend)
base_audio: str = sound_agent.run(
    audio_prompt=prompts["audio_prompt"],
    filename=f"{slug}_audio.mp3",
    duration_seconds=120.0
)
print("Audio generated")

# Calculate target duration in seconds
target_seconds: int = duration_hours * 3600

# Loop video to target duration (no audio yet)
print("Looping video to target duration")
looped_video: str = loop_video(
    input_path=base_video,
    output_path=f"assets/videos/{slug}_video_looped.mp4",
    duration_hours=duration_hours
)

# Loop audio to target duration (full 120s audio looped, not 5s!)
print("Looping audio to target duration")
looped_audio: str = loop_audio(
    input_path=base_audio,
    output_path=f"assets/audio/{slug}_audio_looped.mp3",
    target_duration_seconds=target_seconds
)

# Merge looped video + looped audio
print("Merging audio and video")
final_video: str = merge_audio_video(
    video_path=looped_video,
    audio_path=looped_audio,
    output_path=f"assets/videos/{slug}_{duration_hours}h.mp4"
)
print("Merge complete")

print("FULLY AUTOMATED VIDEO READY:", final_video)

# Upload
print("Uploading to YouTube")
video_id: str = upload_video(
    video_path=final_video,
    title=metadata["title"],
    description=metadata["description"],
    tags=metadata["tags"],
    privacy_status="public"
)
print("YOUTUBE VIDEO ID:", video_id)
print(f"https://youtube.com/watch?v={video_id}")
