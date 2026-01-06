import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You generate high-quality prompts for AI image and video generation
for long YouTube ambience videos.

Output MUST be valid JSON with:
- image_prompt
- video_prompt

GLOBAL RULES:
- English only
- No emojis
- No text overlays
- No people
- No animals
- No camera movement
- No camera angle changes
- Camera must be completely static
- Suitable for seamless looping
- Calm, realistic, cinematic ambience

The visual interest must come from environmental details,
not from camera motion.
"""


class PromptAgent:
    def generate(self, concept: dict) -> dict:
        user_prompt = f"""
Create prompts for a long ambience video.

Ambience: {concept['ambience']}
Mood: {concept['mood']}

IMAGE PROMPT REQUIREMENTS:
- Resolution: 1536x1024
- Static camera, eye-level
- Close, dominant focal element (fireplace, window, sky, ocean, etc.)
- Minimal furniture, uncluttered space
- Strong depth through lighting, not objects
- Highly detailed, photorealistic
- Cinematic lighting
- Sharp focus, no blur

VIDEO PROMPT REQUIREMENTS:
- Same framing as image prompt
- Static camera (absolutely no movement)
- Only subtle environmental motion:
  - fire flames flickering
  - smoke or embers
  - rain drops on glass
  - snowflakes drifting
  - stars slowly twinkling
  - soft light flicker
- Extremely slow, natural motion
- Seamless loop friendly
- No transitions, no cuts
"""


        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.6,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )

        return response.choices[0].message.content

    def save(self, prompts: dict):
        os.makedirs("data/prompts", exist_ok=True)

        image_prompt = prompts["image_prompt"]
        video_prompt = prompts["video_prompt"]

        if isinstance(image_prompt, dict):
            image_prompt = "\n".join(
                f"{k}: {v}" for k, v in image_prompt.items()
            )

        if isinstance(video_prompt, dict):
            video_prompt = "\n".join(
                f"{k}: {v}" for k, v in video_prompt.items()
            )

        image_prompt = str(image_prompt)
        video_prompt = str(video_prompt)

        with open("data/prompts/image_prompt.txt", "w", encoding="utf-8") as f:
            f.write(image_prompt)

        with open("data/prompts/video_prompt.txt", "w", encoding="utf-8") as f:
            f.write(video_prompt)
