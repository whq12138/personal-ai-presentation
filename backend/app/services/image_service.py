"""
Image Generation Pipeline — extracts image_prompt from Slide-JSON
and resolves them to actual image URLs via configured image provider.

Supported providers:
- openai (DALL-E 3)
- dashscope (Alibaba Tongyi Wanxiang)
- stability (Stable Diffusion)
- none (skip generation, keep placeholders)
"""

import logging
import asyncio
from typing import Optional

from openai import AsyncOpenAI

from app.config import get_settings
from app.models.slide import Presentation, Slide

logger = logging.getLogger(__name__)

# Placeholder image URLs by layout type (fallback when no provider configured)
PLACEHOLDER_IMAGES: dict[str, str] = {
    "title": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1280&h=720&fit=crop",
    "two-column": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1280&h=720&fit=crop",
    "highlight-number": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1280&h=720&fit=crop",
    "table": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1280&h=720&fit=crop",
    "bullet-list": "https://images.unsplash.com/photo-1512758017271-d7b84c2113f1?w=1280&h=720&fit=crop",
}


class ImageService:
    """Resolves image_prompt fields to actual image URLs."""

    def __init__(self):
        settings = get_settings()
        self.provider = settings.IMAGE_PROVIDER
        self.api_endpoint = settings.IMAGE_API_ENDPOINT
        self.api_key = settings.IMAGE_API_KEY
        self.model = settings.IMAGE_MODEL
        self.default_width = settings.IMAGE_DEFAULT_WIDTH
        self.default_height = settings.IMAGE_DEFAULT_HEIGHT

    async def enrich_presentation(self, presentation: Presentation) -> Presentation:
        """
        Process all slides in a presentation and resolve image_prompt fields
        to image URLs. Runs image generation in parallel for all slides.

        Modifies the presentation in-place and returns it.
        """
        # Collect slides that need images
        slides_to_process = [
            (i, slide)
            for i, slide in enumerate(presentation.slides)
            if slide.image_prompt and not slide.image_url
        ]

        if not slides_to_process:
            logger.info("No slides require image generation")
            return presentation

        logger.info(f"Processing images for {len(slides_to_process)} slides")

        if self.provider == "none" or not self.api_key:
            # Use placeholder images
            for i, slide in slides_to_process:
                placeholder = PLACEHOLDER_IMAGES.get(
                    slide.layout.value if hasattr(slide.layout, 'value') else str(slide.layout),
                    PLACEHOLDER_IMAGES["title"],
                )
                presentation.slides[i].image_url = placeholder
                presentation.slides[i].background = (
                    presentation.slides[i].background.model_copy(update={"imageUrl": placeholder})
                    if presentation.slides[i].background
                    else type(presentation.slides[i].background).model_validate({"imageUrl": placeholder})
                ) if hasattr(presentation.slides[i], 'background') else None
            return presentation

        # Generate images in parallel
        tasks = [
            self._generate_image(slide.image_prompt, slide.id)
            for _, slide in slides_to_process
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for (i, _), result in zip(slides_to_process, results):
            if isinstance(result, Exception):
                logger.error(f"Image generation failed for slide {presentation.slides[i].id}: {result}")
                # Fall back to placeholder
                layout = presentation.slides[i].layout.value if hasattr(presentation.slides[i].layout, 'value') else str(presentation.slides[i].layout)
                presentation.slides[i].image_url = PLACEHOLDER_IMAGES.get(layout, PLACEHOLDER_IMAGES["title"])
            else:
                presentation.slides[i].image_url = result

        return presentation

    async def _generate_image(self, prompt: str, slide_id: str) -> str:
        """
        Generate an image URL from a text prompt using the configured provider.

        Returns:
            Image URL string
        """
        if self.provider == "openai":
            return await self._generate_openai(prompt, slide_id)
        elif self.provider == "dashscope":
            return await self._generate_dashscope(prompt, slide_id)
        else:
            logger.warning(f"Unknown image provider: {self.provider}, using placeholder")
            return PLACEHOLDER_IMAGES["title"]

    async def _generate_openai(self, prompt: str, slide_id: str) -> str:
        """Generate image via OpenAI DALL-E."""
        client = AsyncOpenAI(api_key=self.api_key)
        try:
            response = await client.images.generate(
                model=self.model,
                prompt=(
                    f"Presentation slide background, professional and clean: {prompt}"
                )[:1000],  # DALL-E prompt length limit
                n=1,
                size="1792x1024",  # close to 16:9
                quality="standard",
            )
            url = response.data[0].url
            logger.info(f"Generated DALL-E image for slide {slide_id}: {url}")
            return url or PLACEHOLDER_IMAGES["title"]
        except Exception as e:
            logger.error(f"DALL-E generation failed for slide {slide_id}: {e}")
            raise

    async def _generate_dashscope(self, prompt: str, slide_id: str) -> str:
        """
        Generate image via Alibaba DashScope (Tongyi Wanxiang).
        Uses the DashScope REST API directly.
        """
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model or "wanx-v1",
            "input": {
                "prompt": f"Professional presentation background, clean design: {prompt}"[:500],
            },
            "parameters": {
                "size": f"{self.default_width}*{self.default_height}",
                "n": 1,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_endpoint or "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            # Extract URL from DashScope response
            results = data.get("output", {}).get("results", [])
            if results and results[0].get("url"):
                url = results[0]["url"]
                logger.info(f"Generated DashScope image for slide {slide_id}: {url}")
                return url

        logger.warning("DashScope returned no image URL, using placeholder")
        return PLACEHOLDER_IMAGES["title"]


# Singleton
_image_service: Optional[ImageService] = None


def get_image_service() -> ImageService:
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service
