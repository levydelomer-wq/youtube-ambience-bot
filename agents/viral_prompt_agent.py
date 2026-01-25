import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from bot_types import Concept, Prompts

load_dotenv()

client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You generate high-quality prompts for AI image and video generation
for viral YouTube Shorts content.

Output MUST be valid JSON with:
- image_prompt
- video_prompt

GLOBAL RULES:
- English only
- No emojis
- No text overlays
- No real people (toys, robots, animated characters OK)
- Visually striking and attention-grabbing
- Optimized for vertical/portrait format
- Entertainment-focused, not ambient

The goal is MAXIMUM engagement and shareability.
"""


class ViralPromptAgent:
    def generate(self, concept: Concept, image_resolution: str = "1024x1792") -> Prompts:
        user_prompt = f"""
Create prompts for a viral YouTube Short (under 60 seconds).

Subject: {concept['ambience']}
Vibe: {concept['mood']}

IMAGE PROMPT REQUIREMENTS:
- Resolution: {image_resolution} (portrait/vertical)
- Center the subject prominently
- Eye-catching colors and contrast
- Clean background that doesn't distract
- Highly detailed, sharp focus
- Dramatic or playful lighting
- The subject should fill most of the frame

VIDEO PROMPT REQUIREMENTS:
- Dynamic motion is encouraged
- The subject should move/animate in an entertaining way
- Loopable if possible (satisfying to rewatch)
- Quick, engaging motion that hooks viewers
- Fun, energetic, or oddly satisfying movement
- No camera movement (subject moves, camera stays still)
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)
