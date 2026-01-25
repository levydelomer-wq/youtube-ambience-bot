from typing import cast

import replicate
from replicate.helpers import FileOutput

from agents.progress import report
from audio_backends.base import AudioBackend

MAX_DURATION_SECONDS: float = 190.0


class ReplicateAudioBackend(AudioBackend):
    def generate(self, audio_prompt: str, duration_seconds: float) -> str:
        if duration_seconds > MAX_DURATION_SECONDS:
            duration_seconds = MAX_DURATION_SECONDS
            report(
                "audio-backend",
                f"Duration clamped to {MAX_DURATION_SECONDS}s (Stable Audio limit)"
            )

        report("audio-backend", "Replicate: audio generation started")

        output = cast(FileOutput, replicate.run(
            "stability-ai/stable-audio-2.5",
            input={
                "prompt": audio_prompt,
                "seconds_total": duration_seconds,
            }
        ))

        audio_url: str = output.url
        report("audio-backend", f"Audio generated: {audio_url}")

        return audio_url
