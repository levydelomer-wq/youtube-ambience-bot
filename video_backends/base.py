# backends/base.py
from abc import ABC, abstractmethod

class VideoBackend(ABC):
    @abstractmethod
    def generate(
        self,
        image_path: str,
        video_prompt: str,
        output_path: str
    ) -> str:
        """
        Generate a short loopable video from a canonical image.

        Constraints (VERY IMPORTANT):
        - Image must remain visually identical (no camera movement)
        - Only subtle environmental motion (fire flicker, rain, fog, embers)
        - No scene changes, no cuts
        - Must be loop-friendly (temporal coherence)

        Returns:
            Path to generated video file
        """
        pass