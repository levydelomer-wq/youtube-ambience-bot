import os
import shutil
import requests
from video_backends.base import VideoBackend
from video_backends.replicate import ReplicateVideoBackend
from config import DRY_RUN

REQUEST_TIMEOUT: int = 300  # 5 minutes for large video downloads


class VideoAgent:
    backend: VideoBackend

    def __init__(self, backend: VideoBackend | None = None) -> None:
        self.backend = backend or ReplicateVideoBackend()

    def run(self, image_path: str, video_prompt: str, filename: str) -> str:
        video_url: str = self.backend.generate(
            image_path=image_path,
            video_prompt=video_prompt,
        )

        output_path: str = os.path.join("assets", "videos", filename)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if not DRY_RUN:
            response: requests.Response = requests.get(video_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(response.content)
        else:
            shutil.copy(video_url, output_path)

        return output_path