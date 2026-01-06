import os
import shutil
import requests
from video_backends.replicate import ReplicateVideoBackend
from video_backends.mock import MockVideoBackend
from config import DRY_RUN

class VideoAgent:
    def __init__(self, backend=None):
        self.backend = backend or ReplicateVideoBackend()

    def run(self, image_path, video_prompt, filename):
        video_url = self.backend.generate(
            image_path=image_path,
            video_prompt=video_prompt,
        )

        output_path = os.path.join("assets", "videos", filename)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if not DRY_RUN:
            video_bytes = requests.get(video_url).content
            with open(output_path, "wb") as f:
                f.write(video_bytes)
        else:
            shutil.copy(video_url, output_path)

        return output_path