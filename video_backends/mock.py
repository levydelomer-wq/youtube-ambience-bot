from video_backends.base import VideoBackend

class MockVideoBackend(VideoBackend):
    def generate(self, image_path: str, video_prompt: str) -> str:

        mock_source = "assets/mock/mock_video.mp4"

        return mock_source