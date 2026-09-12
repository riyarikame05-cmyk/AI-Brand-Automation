import os
import time

import requests


REPLICATE_API_URL = "https://api.replicate.com/v1"


# =========================================================
# PROMPT BUILDERS
# =========================================================

def _build_symbol_prompt(
    specification: dict,
    industry: str,
    style: str,
) -> str:

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


    return (
        f"premium professional brand identity symbol "
        f"for the {industry} industry, "
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
        "centered on pure white background, "
        "no company name, "
        "no letters, "
        "no words, "
        "no typography, "
        "no mockup, "
        "no photograph, "
        "no 3d render"
    )


def _build_campaign_prompt(
    specification: dict,
    industry: str,
    style: str,
) -> str:

    concept = specification.get(
        "concept",
        "premium brand campaign",
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


    return (
        f"{concept}, "
        f"professional advertising campaign "
        f"for the {industry} industry, "
        f"{style} visual direction, "
        f"brand color palette "
        f"{primary}, {secondary}, {accent}, "
        "premium commercial art direction, "
        "high-end advertising photography, "
        "intentional composition, "
        "strong visual hierarchy, "
        "professional lighting, "
        "modern brand aesthetic, "
        "social media campaign quality, "
        "website hero image quality, "
        "clean composition, "
        "space available for marketing copy, "
        "no text, "
        "no letters, "
        "no words, "
        "no watermark, "
        "no logo"
    )


def _build_prompt(
    specification: dict,
    industry: str,
    style: str,
    purpose: str,
) -> str:

    purpose = purpose.lower()


    if purpose == "campaign":

        return _build_campaign_prompt(
            specification=specification,
            industry=industry,
            style=style,
        )


    if purpose == "symbol":

        return _build_symbol_prompt(
            specification=specification,
            industry=industry,
            style=style,
        )


    raise ValueError(
        f"Unknown image purpose: {purpose}"
    )


# =========================================================
# REPLICATE IMAGE GENERATION
# =========================================================

def generate_replicate_image(
    specification: dict,
    industry: str,
    style: str,
    purpose: str = "campaign",
) -> bytes:

    token = os.getenv(
        "REPLICATE_API_TOKEN"
    )


    if not token:

        raise RuntimeError(
            "REPLICATE_API_TOKEN is not configured."
        )


    model = os.getenv(
        "REPLICATE_IMAGE_MODEL"
    )


    if not model:

        raise RuntimeError(
            "REPLICATE_IMAGE_MODEL is not configured."
        )


    prompt = _build_prompt(
        specification=specification,
        industry=industry,
        style=style,
        purpose=purpose,
    )


    headers = {
        "Authorization":
        f"Bearer {token}",

        "Content-Type":
        "application/json",

        "Prefer":
        "wait=60",
    }


    response = requests.post(
        (
            f"{REPLICATE_API_URL}/"
            f"models/{model}/predictions"
        ),

        headers=headers,

        json={
            "input": {
                "prompt":
                prompt,
            }
        },

        timeout=90,
    )


    response.raise_for_status()

    prediction = (
        response.json()
    )


    # -----------------------------------------------------
    # POLL UNTIL COMPLETE
    # -----------------------------------------------------

    while prediction.get(
        "status"
    ) not in {
        "succeeded",
        "failed",
        "canceled",
    }:

        poll_url = (
            prediction.get(
                "urls",
                {},
            )
            .get(
                "get"
            )
        )


        if not poll_url:

            raise RuntimeError(
                "Replicate did not provide "
                "a prediction polling URL."
            )


        time.sleep(
            2
        )


        response = requests.get(
            poll_url,

            headers={
                "Authorization":
                f"Bearer {token}",
            },

            timeout=30,
        )


        response.raise_for_status()