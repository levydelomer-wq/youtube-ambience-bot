import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from bot_types import Concept, Prompts

load_dotenv()

client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You generate high-quality prompts for AI image, video, and audio generation
for long YouTube ambience videos.

Output MUST be valid JSON with exactly these three keys:
- image_prompt: a single string (the full prompt text)
- video_prompt: a single string (the full prompt text)
- audio_prompt: a single string (the full prompt text)

Do NOT nest objects. All values must be plain strings.

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
    def generate(self, concept: Concept, image_resolution: str = "1536x1024") -> Prompts:
        user_prompt = f"""
Create prompts for a long ambience video.

Ambience: {concept['ambience']}
Mood: {concept['mood']}

IMAGE PROMPT REQUIREMENTS:
- Resolution: {image_resolution}
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

AUDIO PROMPT REQUIREMENTS:
- Keep it SHORT (under 20 words)
- Describe the ambient soundscape, not sound effects
- Focus on the PRIMARY sound matching the visual scene
- Add mood/atmosphere descriptors: "cozy", "gentle", "soft", "warm", "quiet"
- End with "no music" to prevent musical elements
- Example: "Cozy indoor fireplace crackling, warm fire burning wood, soft gentle flames, quiet winter night ambience, no music"
"""


        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.6,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def save(self, prompts: Prompts) -> None:
        os.makedirs("data/prompts", exist_ok=True)

        image_prompt: str = prompts["image_prompt"]
        video_prompt: str = prompts["video_prompt"]
        audio_prompt: str = prompts["audio_prompt"]

        with open("data/prompts/image_prompt.txt", "w", encoding="utf-8") as f:
            f.write(image_prompt)

        with open("data/prompts/video_prompt.txt", "w", encoding="utf-8") as f:
            f.write(video_prompt)

        with open("data/prompts/audio_prompt.txt", "w", encoding="utf-8") as f:
            f.write(audio_prompt)
