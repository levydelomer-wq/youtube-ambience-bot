from abc import ABC, abstractmethod


class AudioBackend(ABC):
    @abstractmethod
    def generate(self, audio_prompt: str, duration_seconds: float) -> str:
        """
        Generate ambient audio from a text prompt.

        Args:
            audio_prompt: Description of the ambient sounds to generate.
            duration_seconds: Target duration (max 190s for Stable Audio 2.5).

        Returns:
            URL or path to generated audio file.
        """
        pass
