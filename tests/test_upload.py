import os
import pickle
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from utils.upload import get_youtube_client, upload_video, SCOPES, TOKEN_FILE, CLIENT_SECRET


class TestGetYoutubeClient:
    """Tests for get_youtube_client function."""

    def test_loads_credentials_from_token_file(self, tmp_path: Path) -> None:
        """Test that credentials are loaded from existing token file."""
        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_credentials.expired = False

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open()), \
             patch("pickle.load", return_value=mock_credentials), \
             patch("utils.upload.build") as mock_build:

            mock_build.return_value = MagicMock()
            get_youtube_client()

        mock_build.assert_called_once_with("youtube", "v3", credentials=mock_credentials)

    def test_refreshes_expired_credentials(self, tmp_path: Path) -> None:
        """Test that expired credentials are refreshed."""
        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_credentials.expired = True
        mock_credentials.refresh_token = "refresh_token"

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open()), \
             patch("pickle.load", return_value=mock_credentials), \
             patch("pickle.dump"), \
             patch("utils.upload.Request") as mock_request, \
             patch("utils.upload.build") as mock_build:

            mock_build.return_value = MagicMock()
            get_youtube_client()

        mock_credentials.refresh.assert_called_once()

    def test_runs_oauth_flow_when_no_credentials(self) -> None:
        """Test that OAuth flow is triggered when no credentials exist."""
        mock_flow = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_flow.run_local_server.return_value = mock_credentials

        with patch("os.path.exists", return_value=False), \
             patch("utils.upload.InstalledAppFlow") as mock_app_flow, \
             patch("os.makedirs"), \
             patch("builtins.open", mock_open()), \
             patch("pickle.dump"), \
             patch("utils.upload.build") as mock_build:

            mock_app_flow.from_client_secrets_file.return_value = mock_flow
            mock_build.return_value = MagicMock()
            get_youtube_client()

        mock_app_flow.from_client_secrets_file.assert_called_once_with(
            CLIENT_SECRET, SCOPES
        )
        mock_flow.run_local_server.assert_called_once_with(port=0)

    def test_saves_new_credentials_to_token_file(self) -> None:
        """Test that new credentials are saved after OAuth flow."""
        mock_flow = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_flow.run_local_server.return_value = mock_credentials

        with patch("os.path.exists", return_value=False), \
             patch("utils.upload.InstalledAppFlow") as mock_app_flow, \
             patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_open()) as mock_file, \
             patch("pickle.dump") as mock_dump, \
             patch("utils.upload.build") as mock_build:

            mock_app_flow.from_client_secrets_file.return_value = mock_flow
            mock_build.return_value = MagicMock()
            get_youtube_client()

        mock_makedirs.assert_called_once()
        mock_dump.assert_called_once()

    def test_handles_corrupted_token_file(self) -> None:
        """Test that corrupted token file triggers re-authentication."""
        mock_flow = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_flow.run_local_server.return_value = mock_credentials

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=b"corrupted")), \
             patch("pickle.load", side_effect=pickle.UnpicklingError("corrupted")), \
             patch("utils.upload.InstalledAppFlow") as mock_app_flow, \
             patch("os.makedirs"), \
             patch("pickle.dump"), \
             patch("utils.upload.build") as mock_build:

            mock_app_flow.from_client_secrets_file.return_value = mock_flow
            mock_build.return_value = MagicMock()
            get_youtube_client()

        # Should fall back to OAuth flow
        mock_flow.run_local_server.assert_called_once()


class TestUploadVideo:
    """Tests for upload_video function."""

    def test_calls_youtube_api_with_correct_metadata(self, tmp_path: Path) -> None:
        """Test that YouTube API is called with correct video metadata."""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        mock_youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {"id": "video123", "kind": "youtube#video", "etag": "abc"})
        mock_youtube.videos.return_value.insert.return_value = mock_request

        with patch("utils.upload.get_youtube_client", return_value=mock_youtube), \
             patch("utils.upload.MediaFileUpload") as mock_media:

            upload_video(
                video_path=str(video_file),
                title="Test Video",
                description="Test Description",
                tags=["tag1", "tag2"],
                privacy_status="private"
            )

        # Check insert was called with correct body
        insert_call = mock_youtube.videos.return_value.insert.call_args
        body = insert_call.kwargs["body"]
        assert body["snippet"]["title"] == "Test Video"
        assert body["snippet"]["description"] == "Test Description"
        assert body["snippet"]["tags"] == ["tag1", "tag2"]
        assert body["status"]["privacyStatus"] == "private"

    def test_returns_video_id(self, tmp_path: Path) -> None:
        """Test that video ID is returned after upload."""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        mock_youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {"id": "abc123xyz", "kind": "youtube#video", "etag": "etag"})
        mock_youtube.videos.return_value.insert.return_value = mock_request

        with patch("utils.upload.get_youtube_client", return_value=mock_youtube), \
             patch("utils.upload.MediaFileUpload"):

            result = upload_video(
                video_path=str(video_file),
                title="Test",
                description="Desc",
                tags=[]
            )

        assert result == "abc123xyz"

    def test_default_privacy_is_public(self, tmp_path: Path) -> None:
        """Test that default privacy status is public."""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        mock_youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {"id": "vid", "kind": "youtube#video", "etag": "e"})
        mock_youtube.videos.return_value.insert.return_value = mock_request

        with patch("utils.upload.get_youtube_client", return_value=mock_youtube), \
             patch("utils.upload.MediaFileUpload"):

            upload_video(
                video_path=str(video_file),
                title="Test",
                description="Desc",
                tags=[]
            )

        insert_call = mock_youtube.videos.return_value.insert.call_args
        body = insert_call.kwargs["body"]
        assert body["status"]["privacyStatus"] == "public"

    def test_uses_resumable_upload(self, tmp_path: Path) -> None:
        """Test that resumable upload is enabled."""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        mock_youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {"id": "vid", "kind": "youtube#video", "etag": "e"})
        mock_youtube.videos.return_value.insert.return_value = mock_request

        with patch("utils.upload.get_youtube_client", return_value=mock_youtube), \
             patch("utils.upload.MediaFileUpload") as mock_media:

            upload_video(
                video_path=str(video_file),
                title="Test",
                description="Desc",
                tags=[]
            )

        mock_media.assert_called_once()
        media_call = mock_media.call_args
        assert media_call.kwargs["resumable"] is True

    def test_reports_upload_progress(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that upload progress is printed."""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        mock_youtube = MagicMock()
        mock_request = MagicMock()

        # Simulate chunked upload with progress
        mock_progress = MagicMock()
        mock_progress.progress.return_value = 0.5

        mock_request.next_chunk.side_effect = [
            (mock_progress, None),  # First chunk: 50% progress
            (None, {"id": "vid", "kind": "youtube#video", "etag": "e"})  # Complete
        ]
        mock_youtube.videos.return_value.insert.return_value = mock_request

        with patch("utils.upload.get_youtube_client", return_value=mock_youtube), \
             patch("utils.upload.MediaFileUpload"):

            upload_video(
                video_path=str(video_file),
                title="Test",
                description="Desc",
                tags=[]
            )

        captured = capsys.readouterr()
        assert "50%" in captured.out

    def test_sets_music_category(self, tmp_path: Path) -> None:
        """Test that category is set to Music (10)."""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        mock_youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {"id": "vid", "kind": "youtube#video", "etag": "e"})
        mock_youtube.videos.return_value.insert.return_value = mock_request

        with patch("utils.upload.get_youtube_client", return_value=mock_youtube), \
             patch("utils.upload.MediaFileUpload"):

            upload_video(
                video_path=str(video_file),
                title="Test",
                description="Desc",
                tags=[]
            )

        insert_call = mock_youtube.videos.return_value.insert.call_args
        body = insert_call.kwargs["body"]
        assert body["snippet"]["categoryId"] == "10"
