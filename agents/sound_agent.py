import os
import shutil
import requests
from audio_backends.base import AudioBackend
from audio_backends.replicate import ReplicateAudioBackend
from config import DRY_RUN

REQUEST_TIMEOUT: int = 120  # 2 minutes for audio downloads


class SoundAgent:
    backend: AudioBackend

    def __init__(self, backend: AudioBackend | None = None) -> None:
        self.backend = backend or ReplicateAudioBackend()

    def run(self, audio_prompt: str, filename: str, duration_seconds: float = 120.0) -> str:
        """
        Generate ambient audio and save to local file.

        Args:
            audio_prompt: Description of ambient sounds to generate.
            filename: Output filename (saved to assets/audio/).
            duration_seconds: Target duration (will be clamped to backend limits).

        Returns:
            Path to the saved audio file.
        """
        audio_url: str = self.backend.generate(
            audio_prompt=audio_prompt,
            duration_seconds=duration_seconds,
        )

        output_path: str = os.path.join("assets", "audio", filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if not DRY_RUN:
            response: requests.Response = requests.get(audio_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(response.content)
        else:
            shutil.copy(audio_url, output_path)

        return output_path
