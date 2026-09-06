import random
from urllib.parse import quote

import requests


POLLINATIONS_URL = "https://image.pollinations.ai/prompt"


def generate_flux_symbol(
    specification: dict,
    industry: str,
    style: str,
) -> bytes:
    """
    Generate a high-quality brand symbol with FLUX.

    Typography is intentionally excluded.
    The deterministic renderer should handle company text.
    """

    seed = random.randint(1, 2_000_000_000)

    concept = specification.get(
        "concept",
        "distinctive professional brand symbol",
    )

    logo_type = specification.get(
        "logo_type",
        "abstract",
    )

    shape = specification.get(
        "shape",
        "geometric",
    )

    primary = specification.get(
        "primary_color",
        "#111827",
    )

    secondary = specification.get(
        "secondary_color",
        "#4F46E5",
    )

    accent = specification.get(
        "accent_color",
        "#06B6D4",
    )

    prompt = (
        f"premium professional brand identity symbol for the {industry} industry, "
        f"{concept}, "
        f"{style} aesthetic, "
        f"{logo_type} logo concept, "
        f"{shape} inspired geometry, "
        f"color palette {primary}, {secondary}, {accent}, "
        "single isolated symbol, "
        "minimal vector aesthetic, "
        "strong silhouette, "
        "balanced negative space, "
        "precise clean geometry, "
        "flat solid colors, "
        "timeless corporate identity, "
        "award winning branding studio quality, "
        "centered on pure white background, "
        "no company name, "
        "no letters, "
        "no words, "
        "no typography, "
        "no mockup, "
        "no photograph, "
        "no 3d render"
    )

    url = (
        f"{POLLINATIONS_URL}/"
        f"{quote(prompt, safe='')}"
    )

    params = {
        "width": 1024,
        "height": 1024,
        "seed": seed,
        "model": "flux",
        "enhance": "true",
        "nologo": "true",
    }

    response = requests.get(
        url,
        params=params,
        timeout=180,
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "content-type",
        "",
    ).lower()

    if not content_type.startswith("image/"):
        raise RuntimeError(
            "FLUX provider did not return an image."
        )

    if len(response.content) < 1000:
        raise RuntimeError(
            "FLUX provider returned invalid image data."
        )

    return response.content