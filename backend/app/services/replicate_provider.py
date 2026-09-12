import os
import time

import requests


REPLICATE_API_URL = "https://api.replicate.com/v1"


def _build_prompt(
    specification: dict,
    industry: str,
    style: str,
) -> str:
    concept = specification.get(
        "concept",
        "distinctive professional brand symbol",
    )
    logo_type = specification.get("logo_type", "abstract")
    shape = specification.get("shape", "geometric")
    primary = specification.get("primary_color", "#111827")
    secondary = specification.get("secondary_color", "#4F46E5")
    accent = specification.get("accent_color", "#06B6D4")

    return (
        f"premium professional brand identity symbol for the {industry} industry, "
        f"{concept}, {style} aesthetic, {logo_type} logo concept, "
        f"{shape} inspired geometry, "
        f"color palette {primary}, {secondary}, {accent}, "
        "single isolated symbol, minimal vector aesthetic, "
        "strong silhouette, balanced negative space, "
        "precise clean geometry, flat solid colors, "
        "centered on pure white background, "
        "no company name, no letters, no words, no typography, "
        "no mockup, no photograph, no 3d render"
    )


def generate_replicate_image(
    specification: dict,
    industry: str,
    style: str,
) -> bytes:
    token = os.getenv("REPLICATE_API_TOKEN")

    if not token:
        raise RuntimeError(
            "REPLICATE_API_TOKEN is not configured."
        )

    model = os.getenv("REPLICATE_IMAGE_MODEL")

    if not model:
        raise RuntimeError(
            "REPLICATE_IMAGE_MODEL is not configured."
        )

    prompt = _build_prompt(specification, industry, style)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "wait=60",
    }

    response = requests.post(
        f"{REPLICATE_API_URL}/models/{model}/predictions",
        headers=headers,
        json={
            "input": {
                "prompt": prompt,
            }
        },
        timeout=90,
    )

    response.raise_for_status()
    prediction = response.json()

    # Some predictions finish immediately; others need polling.
    while prediction.get("status") not in {
        "succeeded",
        "failed",
        "canceled",
    }:
        poll_url = prediction.get("urls", {}).get("get")

        if not poll_url:
            raise RuntimeError(
                "Replicate did not provide a prediction polling URL."
            )

        time.sleep(2)

        response = requests.get(
            poll_url,
            headers={
                "Authorization": f"Bearer {token}",
            },
            timeout=30,
        )
        response.raise_for_status()
        prediction = response.json()

    if prediction.get("status") != "succeeded":
        raise RuntimeError(
            f"Replicate generation failed: "
            f"{prediction.get('error') or prediction.get('status')}"
        )

    output = prediction.get("output")

    if isinstance(output, list):
        output = output[0] if output else None

    if not isinstance(output, str):
        raise RuntimeError(
            "Replicate did not return an image URL."
        )

    image_response = requests.get(
        output,
        timeout=60,
    )
    image_response.raise_for_status()

    content_type = image_response.headers.get(
        "content-type",
        "",
    ).lower()

    if not content_type.startswith("image/"):
        raise RuntimeError(
            "Replicate output was not an image."
        )

    return image_response.content