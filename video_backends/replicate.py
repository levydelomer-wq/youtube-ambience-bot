from typing import cast

import replicate
from replicate.helpers import FileOutput

from agents.progress import report
from video_backends.base import VideoBackend


class ReplicateVideoBackend(VideoBackend):
    def generate(
        self,
        image_path: str,
        video_prompt: str,
    ) -> str:
        report("video-backend", "Replicate: image → video generation started")

        with open(image_path, "rb") as image_file:
            output = cast(FileOutput, replicate.run(
                "wavespeedai/wan-2.1-i2v-480p",
                input={
                    "image": image_file,
                    "prompt": video_prompt,
                    "fps": 6
                }
            ))

        video_url = output.url
        report("video-backend", f"Downloading video from {video_url}")

        return video_url