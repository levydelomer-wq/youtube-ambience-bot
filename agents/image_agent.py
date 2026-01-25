import base64
import os
from openai import OpenAI
from dotenv import load_dotenv
from agents.progress import report
from agents.prompt_utils import flatten_prompt


load_dotenv()

client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ImageAgent:
    output_dir: str

    def __init__(self) -> None:
        self.output_dir = "assets/images"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self, image_prompt: str, filename: str = "canonical_4k.png", size: str = "1536x1024") -> str:
        report("image", "Preparing image generation request")

        report("image", "Sending request to OpenAI image API")
        normalized_prompt = flatten_prompt(image_prompt)

        result = client.images.generate(
            model="gpt-image-1",
            prompt=normalized_prompt,
            size=size
        )

        if not result.data:
            raise RuntimeError("OpenAI image API returned empty response")

        report("image", "Decoding image")
        image_base64 = result.data[0].b64_json
        if not image_base64:
            raise RuntimeError("OpenAI image API returned no image data")

        image_bytes: bytes = base64.b64decode(image_base64)

        path: str = os.path.join(self.output_dir, filename)

        report("image", "Saving canonical image")
        with open(path, "wb") as f:
            f.write(image_bytes)

        report("image", f"Image saved: {path}")

        return path