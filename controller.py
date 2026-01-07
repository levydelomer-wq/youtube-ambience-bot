from agents.metadata_agent import MetadataAgent
from agents.prompt_agent import PromptAgent
from agents.image_agent import ImageAgent
from agents.video_agent import VideoAgent
from bot_types import Concept, Metadata, Prompts
from config import DRY_RUN
from video_backends.mock import MockVideoBackend
from video_backends.base import VideoBackend
from utils.loop import loop_video
from utils.upload import upload_video
from utils.upscale import upscale_to_4k


concept: Concept = {
    "ambience": "cozy fireplace",
    "mood": "warm, relaxing, winter night",
    "duration": "10 hours"
}

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
        filename="fireplace_4k_master.png"
    )

# Base video
video_backend: VideoBackend | None = MockVideoBackend() if DRY_RUN else None
video_agent: VideoAgent = VideoAgent(backend=video_backend)
base_video: str = video_agent.run(
    image_path=image_path,
    video_prompt=prompts["video_prompt"],
    filename="fireplace_video.mp4"
)
# upscaled_video = upscale_to_4k(
#     base_video,
#     "video_4k.mp4"
# )


# Loop to 2 hours
final_video: str = loop_video(
    input_path=base_video,  # upscaled_video,
    output_path="assets/videos/fireplace_2h.mp4",
    duration_hours=2
)

print("FULLY AUTOMATED VIDEO READY:", final_video)

# upload
# video_id: str = upload_video(
#     video_path=final_video,
#     title=metadata["title"],
#     description=metadata["description"],
#     tags=metadata["tags"],
#     privacy_status="public"
# )

# print("YOUTUBE VIDEO ID:", video_id)
