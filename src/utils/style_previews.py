"""
Style Preview System for Enhanced UX
Generate and cache preview images for each video style
"""
import os
import time
import json
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from services.kie_client import generate_image

@dataclass
class StylePreview:
    """Style preview configuration"""
    style_id: str
    style_name: str
    category: str
    prompt_enhancement: str
    negative_enhancement: str
    demo_scene: str
    color_palette: List[str]
    keywords: List[str]

class StylePreviewManager:
    """Manages style previews with caching and generation"""

    def __init__(self, media_dir: str = "/app/media"):
        self.media_dir = Path(media_dir)
        self.previews_dir = self.media_dir / "previews"
        self.previews_dir.mkdir(parents=True, exist_ok=True)

        # Style preview configurations
        self.style_configs = {
            "cinematic_realism": StylePreview(
                style_id="cinematic_realism",
                style_name="Cinematic Realism",
                category="realistic",
                prompt_enhancement="masterpiece, 8k, professional photography, award winning",
                negative_enhancement="blurry, low quality, amateur, oversaturated",
                demo_scene="A majestic sunset over a modern city skyline with glass buildings reflecting golden light",
                color_palette=["#FF6B35", "#F7931E", "#FCEE21", "#8CC63F", "#00A652"],
                keywords=["cinematic", "realistic", "professional", "dramatic lighting"]
            ),
            "stylized_3d": StylePreview(
                style_id="stylized_3d",
                style_name="Stylized 3D (Pixar-lite)",
                category="animated",
                prompt_enhancement="pixar style, disney animation, 3d render, vibrant colors, charming",
                negative_enhancement="photorealistic, realistic texture, dark lighting, grainy",
                demo_scene="A friendly robot character in a colorful futuristic city, 3d animation style",
                color_palette=["#FF6B9D", "#C44569", "#723C70", "#5C527F", "#355C7D"],
                keywords=["3d", "animation", "pixar", "colorful", "character"]
            ),
            "anime": StylePreview(
                style_id="anime",
                style_name="Anime",
                category="animated",
                prompt_enhancement="anime art style, manga, studio ghibli, cel shading, detailed line art",
                negative_enhancement="realistic, 3d render, western cartoon, blurry lines",
                demo_scene="A young anime character standing under cherry blossom trees in traditional Japanese setting",
                color_palette=["#FF6B6B", "#FF9F40", "#FFEB3B", "#66BB6A", "#42A5F5"],
                keywords=["anime", "manga", "japanese", "cel shaded", "expressive"]
            ),
            "documentary_grit": StylePreview(
                style_id="documentary_grit",
                style_name="Documentary Grit",
                category="realistic",
                prompt_enhancement="documentary photography, national geographic, authentic, raw emotion",
                negative_enhancement="staged, polished, studio lighting, over edited, artificial",
                demo_scene="A candid street photographer capturing daily life in a bustling marketplace",
                color_palette=["#424242", "#616161", "#757575", "#9E9E9E", "#BDBDBD"],
                keywords=["documentary", "authentic", "raw", "street photography", "real life"]
            ),
            "film_noir": StylePreview(
                style_id="film_noir",
                style_name="Film Noir",
                category="vintage",
                prompt_enhancement="black and white film noir, classic cinema, dramatic shadows, mystery",
                negative_enhancement="color, bright lighting, modern, digital, clean",
                demo_scene="A detective in a trench coat under a single streetlight in a dark alley with rain",
                color_palette=["#000000", "#212121", "#424242", "#616161", "#757575"],
                keywords=["noir", "black white", "dramatic", "mystery", "classic film"]
            ),
            "retro_vhs": StylePreview(
                style_id="retro_vhs",
                style_name="Retro VHS 90s",
                category="vintage",
                prompt_enhancement="1990s vhs aesthetic, retro video, analog tv, scanlines, chromatic aberration",
                negative_enhancement="modern digital, 4k, clean, sharp, hdr",
                demo_scene="A 1990s family vacation home video with period clothing and vintage car",
                color_palette=["#E91E63", "#9C27B0", "#673AB7", "#3F51B5", "#FF5722"],
                keywords=["retro", "vhs", "90s", "analog", "vintage video"]
            ),
            "fantasy_illustration": StylePreview(
                style_id="fantasy_illustration",
                style_name="Fantasy Illustration",
                category="artistic",
                prompt_enhancement="epic fantasy art, book illustration, oil painting, magical, ethereal",
                negative_enhancement="photorealistic, modern, simple, minimal, photograph",
                demo_scene="A powerful wizard casting spells in an ancient library with floating books and magical energy",
                color_palette=["#6A1B9A", "#7B1FA2", "#8E24AA", "#AB47BC", "#CE93D8"],
                keywords=["fantasy", "illustration", "magical", "ethereal", "painting"]
            )
        }

    def get_preview_cache_path(self, style_id: str) -> Path:
        """Get cached preview image path for a style"""
        return self.previews_dir / f"{style_id}_preview.jpg"

    def get_preview_metadata_path(self, style_id: str) -> Path:
        """Get preview metadata path"""
        return self.previews_dir / f"{style_id}_metadata.json"

    def is_preview_cached(self, style_id: str, max_age_hours: int = 24) -> bool:
        """Check if preview exists and is fresh"""
        preview_path = self.get_preview_cache_path(style_id)
        metadata_path = self.get_preview_metadata_path(style_id)

        if not preview_path.exists() or not metadata_path.exists():
            return False

        # Check age
        age_hours = (time.time() - preview_path.stat().st_mtime) / 3600
        return age_hours < max_age_hours

    def generate_preview_prompt(self, style_config: StylePreview) -> str:
        """Generate enhanced prompt for style preview"""
        base_prompt = style_config.demo_scene
        enhancement = style_config.prompt_enhancement

        return f"{base_prompt}, {enhancement}"

    def generate_preview_negative(self, style_config: StylePreview) -> str:
        """Generate enhanced negative prompt for style preview"""
        base_negative = "blurry, low quality, bad lighting, watermark, text, signature"
        enhancement = style_config.negative_enhancement

        return f"{base_negative}, {enhancement}"

    async def generate_style_preview(self, style_id: str, force_refresh: bool = False) -> Dict[str, any]:
        """Generate or retrieve cached preview for a style"""
        if style_id not in self.style_configs:
            raise ValueError(f"Unknown style: {style_id}")

        style_config = self.style_configs[style_id]

        # Check cache first
        if not force_refresh and self.is_preview_cached(style_id):
            return await self._load_cached_preview(style_id)

        # Generate new preview
        try:
            preview_url = await generate_image(
                prompt=self.generate_preview_prompt(style_config),
                negative=self.generate_preview_negative(style_config),
                seed=hash(style_id) % 10000,  # Consistent seed per style
                aspect_ratio="9:16",
                quality="high",
                model="gpt4o-image"
            )

            # Save metadata
            metadata = {
                "style_id": style_id,
                "style_name": style_config.style_name,
                "category": style_config.category,
                "demo_scene": style_config.demo_scene,
                "prompt_used": self.generate_preview_prompt(style_config),
                "negative_used": self.generate_preview_negative(style_config),
                "preview_url": preview_url,
                "generated_at": time.time(),
                "color_palette": style_config.color_palette,
                "keywords": style_config.keywords
            }

            # Save metadata file
            metadata_path = self.get_preview_metadata_path(style_id)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            return metadata

        except Exception as e:
            # Return fallback preview
            return await self._generate_fallback_preview(style_id, str(e))

    async def _load_cached_preview(self, style_id: str) -> Dict[str, any]:
        """Load cached preview metadata"""
        metadata_path = self.get_preview_metadata_path(style_id)

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        # Add cached flag
        metadata["cached"] = True
        return metadata

    async def _generate_fallback_preview(self, style_id: str, error: str) -> Dict[str, any]:
        """Generate fallback preview when generation fails"""
        style_config = self.style_configs[style_id]

        return {
            "style_id": style_id,
            "style_name": style_config.style_name,
            "category": style_config.category,
            "preview_url": f"https://picsum.photos/1080/1920?random={hash(style_id) % 1000}",
            "fallback": True,
            "error": error,
            "generated_at": time.time(),
            "color_palette": style_config.color_palette,
            "keywords": style_config.keywords
        }

    async def generate_all_previews(self, force_refresh: bool = False) -> List[Dict[str, any]]:
        """Generate previews for all styles"""
        tasks = []
        for style_id in self.style_configs.keys():
            task = self.generate_style_preview(style_id, force_refresh)
            tasks.append(task)

        previews = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter exceptions
        valid_previews = []
        for preview in previews:
            if isinstance(preview, Exception):
                print(f"Preview generation error: {preview}")
                continue
            valid_previews.append(preview)

        return valid_previews

    def get_style_overview(self) -> Dict[str, any]:
        """Get overview of all available styles"""
        styles = []
        for style_id, config in self.style_configs.items():
            has_cached = self.is_preview_cached(style_id)

            styles.append({
                "id": style_id,
                "name": config.style_name,
                "category": config.category,
                "demo_scene": config.demo_scene,
                "color_palette": config.color_palette,
                "keywords": config.keywords,
                "has_cached_preview": has_cached
            })

        return {
            "total_styles": len(styles),
            "categories": list(set(s["category"] for s in styles)),
            "styles": styles
        }

# Global preview manager instance
preview_manager = StylePreviewManager()