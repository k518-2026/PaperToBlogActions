import io
import os
import base64
import logging
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class GeminiImageGenerator:
    """
    Generates educational infographic / conceptual illustrations using Gemini Image Generation
    (gemini-3.1-flash-image or imagen-3.0-generate-002) via the google-genai SDK.
    Includes an automatic PIL banner fallback to guarantee image delivery.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-3.1-flash-image"):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate_image(self, prompt: str, output_path: Path, title: str = "") -> Optional[Path]:
        """
        Generate image for the paper and save to output_path.
        """
        refined_prompt = (
            f"{prompt}. "
            f"Style: Clean modern isometric 3D illustration, educational technology, "
            f"computational thinking, vibrant pleasing colors, soft lighting, 16:9 aspect ratio. "
            f"Important: Do not render any readable text, letters, or gibberish typography."
        )

        logger.info(f"Generating image with prompt: {refined_prompt[:120]}...")

        # Strategy 1: Try client.interactions.create (Gemini native image models)
        try:
            logger.info(f"Attempting image generation via interactions API ({self.model_name})...")
            interaction = self.client.interactions.create(
                model=self.model_name,
                input=refined_prompt
            )
            if hasattr(interaction, "output_image") and interaction.output_image:
                image_data = interaction.output_image.data
                image_bytes = base64.b64decode(image_data) if isinstance(image_data, str) else image_data
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                logger.info(f"Successfully generated image via interactions API: {output_path}")
                return output_path
        except Exception as e:
            logger.warning(f"Interactions image generation attempt failed: {e}. Trying imagen-3.0...")

        # Strategy 2: Try client.models.generate_images (Imagen 3)
        try:
            logger.info("Attempting image generation via models.generate_images (imagen-3.0-generate-002)...")
            result = self.client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=refined_prompt,
                config={
                    "number_of_images": 1,
                    "output_mime_type": "image/png",
                    "aspect_ratio": "16:9"
                }
            )
            if result.generated_images:
                img_bytes = result.generated_images[0].image.image_bytes
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                logger.info(f"Successfully generated image via Imagen 3: {output_path}")
                return output_path
        except Exception as e:
            logger.warning(f"Imagen 3 generation attempt failed: {e}. Falling back to styled placeholder...")

        # Strategy 3: Graceful fallback - generate an aesthetic modern graphic banner
        try:
            logger.info("Creating fallback modern educational illustration banner...")
            return self._create_fallback_banner(title or "Research Paper Summary", output_path)
        except Exception as e:
            logger.error(f"Fallback banner creation failed: {e}")
            return None

    def _create_fallback_banner(self, text: str, output_path: Path) -> Path:
        """Create a clean 16:9 SVG-like modern graphic banner when AI generation is unavailable."""
        width, height = 1280, 720
        # Gradient background (blue-indigo theme)
        image = Image.new("RGB", (width, height), color=(30, 41, 59))
        draw = ImageDraw.Draw(image)

        # Draw decorative soft shapes
        draw.ellipse([800, -100, 1400, 500], fill=(59, 130, 246, 60))
        draw.ellipse([100, 400, 700, 1000], fill=(99, 102, 241, 60))
        draw.rounded_rectangle([100, 80, 1180, 640], radius=24, outline=(147, 197, 253), width=3)

        # Draw icon/badge
        draw.rounded_rectangle([140, 120, 480, 180], radius=12, fill=(37, 99, 235))
        draw.text((160, 135), "RESEARCH HIGHLIGHT", fill=(255, 255, 255))

        # Truncate text for title
        display_title = (text[:45] + "...") if len(text) > 45 else text
        draw.text((140, 240), display_title, fill=(241, 245, 249))
        draw.text((140, 340), "Computer Science & Programming Education", fill=(148, 163, 184))
        draw.text((140, 400), "Computational Thinking Insights", fill=(96, 165, 250))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, "PNG")
        return output_path
