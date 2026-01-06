import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You generate YouTube metadata for long ambience videos.
Output MUST be valid JSON with keys:
- title
- description
- tags (array of strings)
"""

class MetadataAgent:
    def generate(self, concept: dict) -> dict:
        user_prompt = f"""
Create metadata for a {concept['duration']} YouTube ambience video.

Ambience: {concept['ambience']}
Mood: {concept['mood']}

Rules:
- English only
- Calm, SEO-friendly
- No emojis
- Description should include hashtags
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def save(self, metadata: dict):
        os.makedirs("data/metadata", exist_ok=True)

        with open("data/metadata/title.txt", "w", encoding="utf-8") as f:
            f.write(metadata["title"])

        with open("data/metadata/description.txt", "w", encoding="utf-8") as f:
            f.write(metadata["description"])

        with open("data/metadata/tags.txt", "w", encoding="utf-8") as f:
            f.write(",".join(metadata["tags"]))
