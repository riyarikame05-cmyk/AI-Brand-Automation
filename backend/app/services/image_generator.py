from __future__ import annotations

from .image_provider import generate_image
from .logo_designer import generate_logo_specification
from .premium_symbol_selector import (
    attach_symbol_provenance,
    select_premium_symbol,
)


# =========================================================
# PUBLIC LOGO GENERATOR
# =========================================================

def generate_logo_image(
    business_name: str,
    industry: str,
    style: str,
    description: str = "",
    direction_index: int | None = None,
    provider: str | None = None,
    palette_name: str = "",
    custom_colors: list[str] | None = None,
    creative_prompt: str = "",
    use_ai_specification: bool = True,
    art_direction: dict | None = None,
) -> dict:
    """
    Generate one complete logo concept.

    Pipeline:

        Business information
            |
            v
        Ollama logo designer
            |
            v
        Structured logo specification
            |
            v
        Hybrid image provider
            |
            +--> cloud provider
            |       |
            |       v
            |   deterministic compositor
            |
            +--> local deterministic renderer
                    |
                    v
                  PNG

    User controls are passed into the Ollama specification:

        style
        palette_name
        custom_colors
        creative_prompt

    direction_index controls structural variation:

        0 = minimal-geometric
        1 = negative-space
        2 = monogram
        3 = abstract-motion
        4 = wordmark
        5 = brand-emblem
    """

    custom_colors = (
        custom_colors
        or []
    )

    print("")
    print("========================================")
    print("[IMAGE GENERATOR] Logo generation")
    print("========================================")

    print(
        f"[IMAGE GENERATOR] Business: "
        f"{business_name}"
    )

    print(
        f"[IMAGE GENERATOR] Industry: "
        f"{industry}"
    )

    print(
        f"[IMAGE GENERATOR] Style: "
        f"{style}"
    )

    print(
        f"[IMAGE GENERATOR] Direction index: "
        f"{direction_index}"
    )

    print(
        f"[IMAGE GENERATOR] Palette: "
        f"{palette_name or 'designer-selected'}"
    )

    if custom_colors:
        print(
            "[IMAGE GENERATOR] Custom colors: "
            + ", ".join(custom_colors)
        )

    if creative_prompt:
        print(
            "[IMAGE GENERATOR] Creative direction: "
            f"{creative_prompt}"
        )

    # =====================================================
    # 1. OLLAMA STRUCTURED DESIGN SPECIFICATION
    # =====================================================

    specification = (
        generate_logo_specification(
            business_name=business_name,
            industry=industry,
            style=style,
            description=description,
            direction_index=direction_index,
            palette_name=palette_name,
            custom_colors=custom_colors,
            creative_prompt=creative_prompt,
            use_ai=use_ai_specification,
        )
    )

    if not isinstance(
        specification,
        dict,
    ):
        raise RuntimeError(
            "Logo designer did not return "
            "a valid specification."
        )

    if isinstance(art_direction, dict):
        allowed_strategies = {
            "bespoke-monogram",
            "negative-space-glyph",
            "abstract-semantic",
            "continuous-line",
            "modular-geometry",
            "signature-emblem",
            "motion-ribbon",
            "typography-led",
            "experimental-fusion",
        }
        allowed_typography = {
            "modern",
            "geometric",
            "elegant",
            "classic",
            "bold",
        }
        allowed_presentations = {
            "stacked",
            "horizontal",
            "emblem",
            "typography-led",
        }

        strategy = str(
            art_direction.get("strategy", "")
        ).strip()
        if strategy in allowed_strategies:
            specification["identity_strategy"] = strategy

        semantic_territory = str(
            art_direction.get(
                "semantic_territory",
                "",
            )
        ).strip()
        if semantic_territory:
            specification[
                "semantic_territory"
            ] = semantic_territory

        industry_form = str(
            art_direction.get(
                "industry_form",
                "",
            )
        ).strip()
        if industry_form:
            specification[
                "industry_form"
            ] = industry_form

        negative_space = str(
            art_direction.get(
                "negative_space_idea",
                "",
            )
        ).strip()
        if negative_space:
            specification[
                "negative_space_idea"
            ] = negative_space

        typography = str(
            art_direction.get(
                "typography_personality",
                "",
            )
        ).strip().lower()
        if typography in allowed_typography:
            specification[
                "typography_personality"
            ] = typography
            specification["font_style"] = typography

        presentation = str(
            art_direction.get(
                "presentation_layout",
                "",
            )
        ).strip().lower()
        if presentation in allowed_presentations:
            specification[
                "presentation_layout"
            ] = presentation
            specification["layout"] = (
                "symbol-left"
                if presentation == "horizontal"
                else "symbol-top"
            )

        specification["sonnet_art_direction"] = {
            "model": "kr/claude-sonnet-4.5",
            "visual_idea": str(
                art_direction.get(
                    "visual_idea",
                    "",
                )
            ).strip(),
            "composition_note": str(
                art_direction.get(
                    "composition_note",
                    "",
                )
            ).strip(),
        }

    print("")
    print(
        "[IMAGE GENERATOR] "
        "Logo specification:"
    )

    print(
        specification
    )

    # =====================================================
    # 2. HYBRID IMAGE GENERATION
    # =====================================================
    #
    # provider="auto":
    #
    # Replicate if configured
    #       |
    #       v failure / unavailable
    # FLUX / Pollinations
    #       |
    #       v failure
    # deterministic local renderer
    #
    # Successful cloud logo artwork is composed with
    # deterministic BrandAI typography by image_provider.py.
    # =====================================================

    premium_symbol = select_premium_symbol(
        specification=specification,
        industry=industry,
        candidate_index=(
            direction_index
            if direction_index is not None
            else 0
        ),
    )

    specification = attach_symbol_provenance(
        specification,
        premium_symbol,
    )

    # Catalog rendering is introduced only after a master has passed
    # ingestion and visual approval. Until then the proven hybrid/local
    # renderer remains the production fallback.
    image_bytes = (
        generate_image(
            provider=provider,
            purpose="symbol",
            specification=specification,
            business_name=business_name,
            industry=industry,
            style=style,
        )
    )

    # =====================================================
    # 3. VALIDATE RETURNED IMAGE
    # =====================================================

    if not isinstance(
        image_bytes,
        (
            bytes,
            bytearray,
        ),
    ):
        raise RuntimeError(
            "Image provider did not return "
            "image bytes."
        )

    if len(
        image_bytes
    ) < 1000:
        raise RuntimeError(
            "Image provider returned "
            "an empty or invalid image."
        )

    print(
        "[IMAGE GENERATOR] "
        "Image generated successfully "
        f"({len(image_bytes)} bytes)"
    )

    return {
        "image_bytes": bytes(
            image_bytes
        ),
        "specification": specification,
    }