import os
import pickle
from typing import TypedDict, NotRequired, cast

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaFileUpload, HttpRequest, MediaUploadProgress

class YouTubeVideoSnippet(TypedDict):
    """Snippet portion of a YouTube video resource."""
    title: str
    description: str
    tags: NotRequired[list[str]]
    categoryId: str
    channelId: str
    channelTitle: str


class YouTubeVideoStatus(TypedDict):
    """Status portion of a YouTube video resource."""
    privacyStatus: str
    uploadStatus: str


class YouTubeVideoResponse(TypedDict):
    """Response from YouTube Data API v3 videos.insert()."""
    id: str
    kind: str
    etag: str
    snippet: NotRequired[YouTubeVideoSnippet]
    status: NotRequired[YouTubeVideoStatus]


SCOPES: list[str] = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE: str = "secrets/youtube_token.pickle"
CLIENT_SECRET: str = "secrets/client_secret.json"


def get_youtube_client() -> Resource:
    """Get an authenticated YouTube API client.

    Returns:
        Authenticated YouTube API resource.
    """
    credentials: Credentials | None = None

    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "rb") as f:
                credentials = pickle.load(f)
        except (pickle.UnpicklingError, EOFError) as e:
            print(f"Warning: Could not load credentials, will re-authenticate: {e}")
            credentials = None

    # Refresh expired credentials if possible
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            with open(TOKEN_FILE, "wb") as f:
                pickle.dump(credentials, f)
        except Exception as e:
            print(f"Warning: Could not refresh credentials: {e}")
            credentials = None

    if not credentials or not credentials.valid:
        flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET, SCOPES
        )
        credentials = cast(Credentials, flow.run_local_server(port=0))

        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(credentials, f)

    return build("youtube", "v3", credentials=credentials)


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy_status: str = "public"
) -> str:
    """Upload a video to YouTube.

    Args:
        video_path: Path to the video file.
        title: Video title.
        description: Video description.
        tags: List of video tags.
        privacy_status: Privacy status (public, private, unlisted).

    Returns:
        The YouTube video ID.
    """
    youtube: Resource = get_youtube_client()

    request: HttpRequest = youtube.videos().insert(  # type: ignore[attr-defined]
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "10"  # Music - appropriate for ambience videos
            },
            "status": {
                "privacyStatus": privacy_status
            }
        },
        media_body=MediaFileUpload(
            video_path,
            chunksize=-1,
            resumable=True
        )
    )

    response: YouTubeVideoResponse | None = None
    while response is None:
        status: MediaUploadProgress | None
        status, chunk_response = request.next_chunk()  # type: ignore[union-attr]
        response = cast(YouTubeVideoResponse | None, chunk_response)
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    print("Upload complete:", response["id"])
    return response["id"]