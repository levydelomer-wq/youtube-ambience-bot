from audio_backends.base import AudioBackend


class MockAudioBackend(AudioBackend):
    def generate(self, audio_prompt: str, duration_seconds: float) -> str:
        mock_source: str = "assets/mock/mock_audio.mp3"
        return mock_source
