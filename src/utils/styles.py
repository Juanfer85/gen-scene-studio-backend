"""
Catálogo de estilos para Gen Scene Studio.
Fuente de verdad centralizada para consistencia entre frontend y backend.
"""

STYLES = {
    "cinematic_realism": {
        "prompt": "cinematic, realistic lighting, soft depth of field, high dynamic range, subtle film grain",
        "negative": "cartoon, overexposed, blurry, plastic skin, oversaturated, watermark, text",
        "meta": {
            "label": "Cinematic Realism",
            "motion": "kenburns",
            "grain": "subtle",
            "aspectRatio": "9:16",
            "category": "realistic"
        },
    },
    "stylized_3d": {
        "prompt": "stylized 3D, soft subsurface scattering, studio lighting, clean materials, expressive characters",
        "negative": "photorealism, harsh shadows, grain, text, watermark",
        "meta": {
            "label": "Stylized 3D (Pixar-lite)",
            "motion": "kenburns",
            "grain": "none",
            "aspectRatio": "9:16",
            "category": "animated"
        },
    },
    "anime": {
        "prompt": "anime style, cel shading, crisp line art, expressive eyes, painterly background, high contrast",
        "negative": "photorealistic, 3D render noise, text overlay",
        "meta": {
            "label": "Anime",
            "motion": "kenburns",
            "grain": "none",
            "aspectRatio": "9:16",
            "category": "animated"
        },
    },
    "documentary_grit": {
        "prompt": "documentary style, handheld feel, available light, authentic textures, minimal grading",
        "negative": "overpolished, studio glamour, artificial lighting look",
        "meta": {
            "label": "Documentary Grit",
            "motion": "handheld",
            "grain": "subtle",
            "aspectRatio": "9:16",
            "category": "realistic"
        },
    },
    "film_noir": {
        "prompt": "black and white film noir, hard light, deep shadows, high contrast, venetian blinds shadows",
        "negative": "color, low contrast, flat lighting, text",
        "meta": {
            "label": "Film Noir",
            "motion": "kenburns",
            "grain": "heavy",
            "aspectRatio": "9:16",
            "category": "vintage"
        },
    },
    "retro_vhs": {
        "prompt": "retro 90s vhs aesthetic, chromatic aberration, scanlines, analog noise, soft focus",
        "negative": "ultra sharp, modern digital clarity",
        "meta": {
            "label": "Retro VHS 90s",
            "motion": "handheld",
            "grain": "heavy",
            "aspectRatio": "9:16",
            "category": "vintage"
        },
    },
    "fantasy_illustration": {
        "prompt": "epic fantasy illustration, painterly brushwork, volumetric lighting, ornate details, dramatic composition",
        "negative": "photorealistic, flat colors, text",
        "meta": {
            "label": "Fantasy Illustration",
            "motion": "kenburns",
            "grain": "none",
            "aspectRatio": "9:16",
            "category": "artistic"
        },
    },
}

def get_style(style_id: str) -> dict:
    """
    Obtiene un estilo por ID, fallback a cinematic_realism si no existe.
    """
    return STYLES.get(style_id, STYLES["cinematic_realism"])

def list_styles() -> list:
    """
    Retorna lista de estilos con sus IDs para el frontend.
    """
    return [{"id": k, **v} for k, v in STYLES.items()]

def get_styles_by_category(category: str) -> list:
    """
    Filtra estilos por categoría.
    """
    return [
        {"id": k, **v}
        for k, v in STYLES.items()
        if v["meta"]["category"] == category
    ]

def get_categories() -> list:
    """
    Retorna lista de categorías disponibles.
    """
    categories = set()
    for style in STYLES.values():
        categories.add(style["meta"]["category"])
    return sorted(list(categories))