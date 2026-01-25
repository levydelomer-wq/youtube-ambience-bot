# GitHub Secrets Setup

To run the automated upload workflow, you need to configure these secrets in your GitHub repository.

Go to: **Settings → Secrets and variables → Actions → New repository secret**

## Required Secrets

### 1. `OPENAI_API_KEY`
Your OpenAI API key for image generation.

### 2. `REPLICATE_API_TOKEN`
Your Replicate API token for video and audio generation.

### 3. `YOUTUBE_CLIENT_SECRET`
The contents of your `secrets/client_secret.json` file from Google Cloud Console.

To get this:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable YouTube Data API v3
3. Create OAuth 2.0 credentials (Desktop app)
4. Download the JSON and paste its contents as this secret

### 4. `YOUTUBE_TOKEN`
Base64-encoded YouTube OAuth token.

To generate this:
```bash
# First, run locally to authenticate
python controller.py

# This creates secrets/youtube_token.pickle
# Then encode it:
base64 secrets/youtube_token.pickle

# Copy the output and paste as YOUTUBE_TOKEN secret
```

## Token Refresh

YouTube tokens expire. If uploads fail with auth errors:
1. Run locally again to refresh the token
2. Re-encode and update the `YOUTUBE_TOKEN` secret

## Manual Trigger

You can manually trigger the workflow:
1. Go to **Actions → Upload Ambience Video**
2. Click **Run workflow**
3. Optionally enter a concept (e.g., "ocean waves")
