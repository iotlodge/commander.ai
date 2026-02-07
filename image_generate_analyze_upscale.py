import base64
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from openai import OpenAI

from dotenv import load_dotenv
settings = load_dotenv()



class ImageProcessor:
    """
    Unified image toolset for Claude Code.
    Supports:
      - Generation via DALL·E
      - Vision analysis
      - Upscaling / variations
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)

    # ---------------------------------------------------------
    # IMAGE GENERATION
    # ---------------------------------------------------------
    def generate_image(self, prompt: str, size: str = "1024x1024", output: str = "generated.png") -> str:
        response = self.client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size
        )

        image_base64 = response.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        Path(output).write_bytes(image_bytes)

        return output

    # ---------------------------------------------------------
    # IMAGE ANALYSIS (VISION)
    # ---------------------------------------------------------
    def analyze_image(self, image_path: str, prompt: str = "Describe this image in detail") -> str:
        image_bytes = Path(image_path).read_bytes()
        encoded = base64.b64encode(image_bytes).decode()

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{encoded}"}
                        }
                    ]
                }
            ]
        )

        return response.choices[0].message.content

    # ---------------------------------------------------------
    # IMAGE UPSCALE / VARIATION
    # ---------------------------------------------------------
    def upscale_image(self, image_path: str, output: str = "upscaled.png") -> str:
        image_bytes = Path(image_path).read_bytes()
        encoded = base64.b64encode(image_bytes).decode()

        response = self.client.images.generate(
            model="gpt-image-1",
            prompt="Upscale this image while preserving content and improving clarity",
            image=encoded
        )

        result = base64.b64decode(response.data[0].b64_json)
        Path(output).write_bytes(result)

        return output


# ---------------------------------------------------------
# CLI INTERFACE FOR CLAUDE CODE
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Image Processing Toolkit for Claude Code")

    subparsers = parser.add_subparsers(dest="command")

    # Generate
    gen = subparsers.add_parser("generate")
    gen.add_argument("--prompt", required=True)
    gen.add_argument("--size", default="1024x1024")
    gen.add_argument("--output", default="generated.png")

    # Analyze
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--image", required=True)
    analyze.add_argument("--prompt", default="Describe this image in detail")

    # Upscale
    upscale = subparsers.add_parser("upscale")
    upscale.add_argument("--image", required=True)
    upscale.add_argument("--output", default="upscaled.png")

    args = parser.parse_args()

    processor = ImageProcessor()

    if args.command == "generate":
        path = processor.generate_image(args.prompt, args.size, args.output)
        print(json.dumps({"file": path}))

    elif args.command == "analyze":
        result = processor.analyze_image(args.image, args.prompt)
        print(json.dumps({"analysis": result}))

    elif args.command == "upscale":
        path = processor.upscale_image(args.image, args.output)
        print(json.dumps({"file": path}))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()