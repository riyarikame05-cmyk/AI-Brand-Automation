from __future__ import annotations

from .image_provider import generate_image
from .logo_designer import generate_logo_specification


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
) -> bytes:
    """
    Generate one logo concept.

    Pipeline:

        Business information
            ↓
        Ollama logo designer
            ↓
        Structured logo specification
            ↓
        Image provider router
            ↓
        Cloud provider OR local renderer
            ↓
        PNG bytes

    direction_index controls the creative direction:

        0 = minimal-geometric
        1 = symbolic-negative-space
        2 = typographic

    The provider router handles local/cloud fallback.
    """

    print("")
    print("========================================")
    print("[IMAGE GENERATOR] Logo generation")
    print("========================================")
    print(f"[IMAGE GENERATOR] Business: {business_name}")
    print(f"[IMAGE GENERATOR] Industry: {industry}")
    print(f"[IMAGE GENERATOR] Style: {style}")
    print(
        f"[IMAGE GENERATOR] Direction index: "
        f"{direction_index}"
    )

    # -----------------------------------------------------
    # 1. Generate structured design specification
    # -----------------------------------------------------

    specification = generate_logo_specification(
        business_name=business_name,
        industry=industry,
        style=style,
        description=description,
        direction_index=direction_index,
    )

    if not isinstance(specification, dict):
        raise RuntimeError(
            "Logo designer did not return a valid specification."
        )

    print("")
    print("[IMAGE GENERATOR] Logo specification:")
    print(specification)

    # -----------------------------------------------------
    # 2. Route generation through the hybrid provider
    # -----------------------------------------------------
    #
    # IMAGE_PROVIDER=local
    #     -> deterministic local logo renderer
    #
    # IMAGE_PROVIDER=replicate
    #     -> Replicate
    #     -> local fallback when configured by router
    #
    # IMAGE_PROVIDER=flux
    #     -> FLUX/Pollinations
    #
    # IMAGE_PROVIDER=auto
    #     -> Replicate
    #     -> FLUX/Pollinations
    #     -> local renderer
    #
    # The image model is asked for a symbol rather than
    # company-name typography because image models can
    # misspell text.
    # -----------------------------------------------------

    image_bytes = generate_image(
        provider=provider,
        purpose="symbol",
        specification=specification,
        business_name=business_name,
        industry=industry,
        style=style,
    )

    # -----------------------------------------------------
    # 3. Validate returned image
    # -----------------------------------------------------

    if not isinstance(
        image_bytes,
        (bytes, bytearray),
    ):
        raise RuntimeError(
            "Image provider did not return image bytes."
        )

    if len(image_bytes) < 100:
        raise RuntimeError(
            "Image provider returned an empty or invalid image."
        )

    print(
        f"[IMAGE GENERATOR] Image generated successfully "
        f"({len(image_bytes)} bytes)"
    )

    return bytes(image_bytes)