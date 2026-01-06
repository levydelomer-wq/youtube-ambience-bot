import base64
import os
from openai import OpenAI
from dotenv import load_dotenv
from agents.progress import report
from agents.prompt_utils import flatten_prompt


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ImageAgent:
    def __init__(self):
        self.output_dir = "assets/images"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self, image_prompt: str, filename: str = "canonical_4k.png"):
        report("image", "Preparing image generation request")

        report("image", "Sending request to OpenAI image API")
        normalized_prompt = flatten_prompt(image_prompt)

        result = client.images.generate(
            model="gpt-image-1",
            prompt=normalized_prompt,
            size="1536x1024"
        )


        report("image", "Decoding image")
        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        path = os.path.join(self.output_dir, filename)

        report("image", "Saving canonical image")
        with open(path, "wb") as f:
            f.write(image_bytes)

        report("image", f"Image saved: {path}")

        return path