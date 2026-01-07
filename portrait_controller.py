from agents.metadata_agent import MetadataAgent
from agents.prompt_agent import PromptAgent
from agents.image_agent import ImageAgent
from agents.video_agent import VideoAgent
from bot_types import Concept, Metadata, Prompts
from config import DRY_RUN
from video_backends.mock import MockVideoBackend
from video_backends.base import VideoBackend

PORTRAIT_SIZE = "1024x1792"

# TODO: Define your concept here - what ambience works best for portrait/vertical videos?
# Consider: shorter attention spans, mobile viewing, visually striking vertical compositions
concept: Concept = {
    "ambience": "",  # e.g., "rainy window at night", "northern lights", "waterfall close-up"
    "mood": "",      # e.g., "mysterious, calming", "awe-inspiring", "meditative"
    "duration": "short"
}

# Metadata
print("Generating metadata")
metadata: Metadata = MetadataAgent().generate(concept)

# Prompts (with portrait resolution)
print("Generating prompts")
prompts: Prompts = PromptAgent().generate(concept, image_resolution=PORTRAIT_SIZE)

# Image (portrait size)
image_path: str
if DRY_RUN:
    image_path = "assets/mock/mock_image.jpg"
else:
    image_path = ImageAgent().run(
        image_prompt=prompts["image_prompt"],
        filename="portrait_image.png",
        size=PORTRAIT_SIZE
    )

# Video (no looping, no upscaling)
video_backend: VideoBackend | None = MockVideoBackend() if DRY_RUN else None
video_agent: VideoAgent = VideoAgent(backend=video_backend)
final_video: str = video_agent.run(
    image_path=image_path,
    video_prompt=prompts["video_prompt"],
    filename="portrait_video.mp4"
)

print("PORTRAIT VIDEO READY:", final_video)
