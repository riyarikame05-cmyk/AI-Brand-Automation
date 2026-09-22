from __future__ import annotations

import os
import time
from typing import Any

import requests


REPLICATE_API_URL = "https://api.replicate.com/v1"

REQUEST_TIMEOUT = 90
DOWNLOAD_TIMEOUT = 90
POLL_TIMEOUT = 30
POLL_INTERVAL = 2
MAX_WAIT_SECONDS = 180


# =========================================================
# SYMBOL PROMPT
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

    creative_direction = specification.get(
        "creative_direction",
        "",
    )

    logo_type = specification.get(
        "logo_type",
        "abstract",
    )

    shape = specification.get(
        "shape",
        "geometric",
    )

    metaphor = specification.get(
        "visual_metaphor",
        "",
    )

    geometry_style = specification.get(
        "geometry_style",
        "clean",
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
        "Design a single professional brand symbol only. "
        "This will later be combined with exact company-name "
        "typography by a separate deterministic design system. "

        f"Industry: {industry}. "
        f"Brand style: {style}. "
        f"Creative direction: {creative_direction}. "
        f"Concept: {concept}. "
        f"Visual metaphor: {metaphor}. "
        f"Logo category: {logo_type}. "
        f"Geometry inspiration: {shape}. "
        f"Geometry style: {geometry_style}. "

        f"Use this color palette as inspiration: "
        f"{primary}, {secondary}, {accent}. "

        "Create one original, distinctive, memorable brand mark. "
        "Strong silhouette. "
        "Simple geometry. "
        "Intentional negative space where appropriate. "
        "Balanced proportions. "
        "Minimal detail. "
        "Scalable visual identity. "
        "Flat vector-style graphic. "
        "Solid colors. "
        "Sharp clean edges. "
        "Centered isolated mark. "
        "Pure white background. "
        "Professional branding studio quality. "

        "IMPORTANT RESTRICTIONS: "
        "Do not write the company name. "
        "Do not generate any words. "
        "Do not generate letters. "
        "Do not generate initials. "
        "Do not generate numbers. "
        "Do not generate captions. "
        "Do not generate typography. "
        "Do not generate a watermark. "
        "Do not generate a signature. "
        "Do not generate provider branding. "
        "Do not show the logo on paper. "
        "Do not show the logo on a wall. "
        "Do not show business cards. "
        "Do not show stationery. "
        "Do not show packaging. "
        "Do not create a mockup. "
        "Do not create a photograph. "
        "Do not create a 3D render. "
        "Do not create shadows under the symbol. "
        "Return only the isolated flat brand symbol "
        "on a clean white background."
    )


# =========================================================
# CAMPAIGN PROMPT
# =========================================================

def _build_campaign_prompt(
    specification: dict,
    industry: str,
    style: str,
) -> str:
    concept = specification.get(
        "concept",
        "premium professional brand campaign",
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
        f"{concept}. "
        f"Professional commercial advertising artwork "
        f"for the {industry} industry. "
        f"{style} visual direction. "

        f"Brand color inspiration: "
        f"{primary}, {secondary}, {accent}. "

        "Premium commercial art direction. "
        "Strong visual hierarchy. "
        "Intentional composition. "
        "Professional lighting. "
        "Modern brand aesthetic. "
        "Website hero image quality. "
        "Social media campaign quality. "
        "Leave intentional negative space for marketing copy. "

        "Do not include visible text. "
        "Do not include letters. "
        "Do not include words. "
        "Do not include watermarks. "
        "Do not include logos."
    )


# =========================================================
# PROMPT ROUTER
# =========================================================

def _build_prompt(
    specification: dict,
    industry: str,
    style: str,
    purpose: str,
) -> str:
    purpose = (
        str(
            purpose
        )
        .strip()
        .lower()
    )

    if purpose == "symbol":
        return _build_symbol_prompt(
            specification=specification,
            industry=industry,
            style=style,
        )

    if purpose == "campaign":
        return _build_campaign_prompt(
            specification=specification,
            industry=industry,
            style=style,
        )

    raise ValueError(
        f"Unknown image purpose: {purpose}"
    )


# =========================================================
# MODEL INPUT
# =========================================================

def _build_model_input(
    model: str,
    prompt: str,
    purpose: str,
) -> dict:
    """
    Build input for the configured Replicate model.

    Current tested target:
        openai/gpt-image-2

    Replicate's current example for this model supports:
        prompt
        aspect_ratio
        input_images

    We do not pass input_images for original generation.
    """

    model = (
        str(
            model
        )
        .strip()
        .lower()
    )

    purpose = (
        str(
            purpose
        )
        .strip()
        .lower()
    )

    # -----------------------------------------------------
    # OPENAI GPT IMAGE 2
    # -----------------------------------------------------

    if model == "openai/gpt-image-2":
        if purpose == "symbol":
            return {
                "prompt": prompt,
                "aspect_ratio": "1:1",
            }

        return {
            "prompt": prompt,
            "aspect_ratio": "16:9",
        }

    # -----------------------------------------------------
    # GENERIC FALLBACK
    # -----------------------------------------------------
    #
    # Other Replicate models may have different schemas.
    # For unknown models we deliberately keep the request
    # minimal instead of assuming unsupported fields.
    # -----------------------------------------------------

    return {
        "prompt": prompt,
    }


# =========================================================
# OUTPUT URL EXTRACTION
# =========================================================

def _extract_output_url(
    output: Any,
) -> str:
    """
    Replicate REST responses usually expose file outputs
    as URLs or lists containing URLs.
    """

    if isinstance(
        output,
        str,
    ):
        return output

    if isinstance(
        output,
        list,
    ):
        for item in output:
            if isinstance(
                item,
                str,
            ):
                return item

            if isinstance(
                item,
                dict,
            ):
                for key in (
                    "url",
                    "image",
                    "output",
                    "file",
                ):
                    value = item.get(
                        key
                    )

                    if isinstance(
                        value,
                        str,
                    ):
                        return value

    if isinstance(
        output,
        dict,
    ):
        for key in (
            "url",
            "image",
            "output",
            "file",
        ):
            value = output.get(
                key
            )

            if isinstance(
                value,
                str,
            ):
                return value

            if isinstance(
                value,
                list,
            ):
                for item in value:
                    if isinstance(
                        item,
                        str,
                    ):
                        return item

                    if isinstance(
                        item,
                        dict,
                    ):
                        item_url = item.get(
                            "url"
                        )

                        if isinstance(
                            item_url,
                            str,
                        ):
                            return item_url

    raise RuntimeError(
        "Replicate completed successfully but did not "
        "return a usable image URL."
    )


# =========================================================
# DOWNLOAD RESULT
# =========================================================

def _download_image(
    url: str,
) -> bytes:
    try:
        response = requests.get(
            url,
            timeout=DOWNLOAD_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise RuntimeError(
            "Could not download Replicate image: "
            f"{error}"
        ) from error

    content_type = (
        response.headers.get(
            "content-type",
            "",
        )
        .lower()
    )

    image_bytes = response.content

    if not isinstance(
        image_bytes,
        (bytes, bytearray),
    ):
        raise RuntimeError(
            "Replicate returned invalid image data."
        )

    if len(image_bytes) < 1000:
        raise RuntimeError(
            "Downloaded Replicate image is too small "
            "or invalid."
        )

    if (
        content_type
        and not content_type.startswith(
            "image/"
        )
        and "octet-stream" not in content_type
    ):
        print(
            "[REPLICATE] Warning: unexpected "
            f"content type: {content_type}"
        )

    return bytes(
        image_bytes
    )


# =========================================================
# ERROR BODY
# =========================================================

def _response_error_body(
    response,
) -> str:
    if response is None:
        return ""

    try:
        return (
            response.text
            or ""
        )[:1000]

    except Exception:
        return ""


# =========================================================
# GENERATE IMAGE
# =========================================================

def generate_replicate_image(
    specification: dict,
    industry: str,
    style: str,
    purpose: str = "campaign",
) -> bytes:
    # =====================================================
    # CONFIGURATION
    # =====================================================

    token = (
        os.getenv(
            "REPLICATE_API_TOKEN",
            "",
        )
        .strip()
    )

    if not token:
        raise RuntimeError(
            "REPLICATE_API_TOKEN is not configured."
        )

    model = (
        os.getenv(
            "REPLICATE_IMAGE_MODEL",
            "",
        )
        .strip()
        .strip("/")
    )

    if not model:
        raise RuntimeError(
            "REPLICATE_IMAGE_MODEL is not configured."
        )

    purpose = (
        str(
            purpose
        )
        .strip()
        .lower()
    )

    # =====================================================
    # PROMPT + MODEL INPUT
    # =====================================================

    prompt = _build_prompt(
        specification=specification,
        industry=industry,
        style=style,
        purpose=purpose,
    )

    model_input = _build_model_input(
        model=model,
        prompt=prompt,
        purpose=purpose,
    )

    print("")
    print(
        "========================================"
    )
    print(
        "[REPLICATE] Image generation"
    )
    print(
        "========================================"
    )
    print(
        f"[REPLICATE] Model: {model}"
    )
    print(
        f"[REPLICATE] Purpose: {purpose}"
    )
    print(
        "[REPLICATE] Creating prediction..."
    )

    # =====================================================
    # AUTH
    # =====================================================

    headers = {
        "Authorization":
            f"Bearer {token}",

        "Content-Type":
            "application/json",

        "Prefer":
            "wait=60",
    }

    # =====================================================
    # CREATE PREDICTION
    # =====================================================

    endpoint = (
        f"{REPLICATE_API_URL}"
        f"/models/{model}/predictions"
    )

    response = None

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json={
                "input":
                    model_input,
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        body = _response_error_body(
            getattr(
                error,
                "response",
                None,
            )
            or response
        )

        raise RuntimeError(
            "Replicate prediction request failed. "
            f"{error}. "
            f"{body}"
        ) from error

    try:
        prediction = response.json()

    except ValueError as error:
        raise RuntimeError(
            "Replicate returned invalid JSON "
            "when creating the prediction."
        ) from error

    # =====================================================
    # POLL
    # =====================================================

    started = time.monotonic()

    while True:
        status = (
            str(
                prediction.get(
                    "status",
                    "",
                )
            )
            .strip()
            .lower()
        )

        print(
            f"[REPLICATE] Status: {status}"
        )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        if status == "succeeded":
            break

        # -------------------------------------------------
        # FAILURE
        # -------------------------------------------------

        if status in {
            "failed",
            "canceled",
        }:
            message = (
                prediction.get(
                    "error"
                )
                or prediction.get(
                    "logs"
                )
                or "Unknown Replicate error."
            )

            raise RuntimeError(
                "Replicate generation "
                f"{status}: {message}"
            )

        # -------------------------------------------------
        # TIMEOUT
        # -------------------------------------------------

        elapsed = (
            time.monotonic()
            - started
        )

        if elapsed > MAX_WAIT_SECONDS:
            raise RuntimeError(
                "Replicate generation timed out "
                f"after {MAX_WAIT_SECONDS} seconds."
            )

        # -------------------------------------------------
        # POLLING URL
        # -------------------------------------------------

        poll_url = (
            prediction
            .get(
                "urls",
                {},
            )
            .get(
                "get"
            )
        )

        if not poll_url:
            raise RuntimeError(
                "Replicate did not provide a prediction "
                "polling URL."
            )

        time.sleep(
            POLL_INTERVAL
        )

        poll_response = None

        try:
            poll_response = requests.get(
                poll_url,
                headers={
                    "Authorization":
                        f"Bearer {token}",
                },
                timeout=POLL_TIMEOUT,
            )

            poll_response.raise_for_status()

        except requests.RequestException as error:
            body = _response_error_body(
                getattr(
                    error,
                    "response",
                    None,
                )
                or poll_response
            )

            raise RuntimeError(
                "Could not poll Replicate prediction. "
                f"{error}. "
                f"{body}"
            ) from error

        try:
            prediction = (
                poll_response.json()
            )

        except ValueError as error:
            raise RuntimeError(
                "Replicate returned invalid JSON "
                "while polling prediction."
            ) from error

    # =====================================================
    # OUTPUT
    # =====================================================

    output = prediction.get(
        "output"
    )

    output_url = _extract_output_url(
        output
    )

    print(
        "[REPLICATE] Prediction succeeded."
    )
    print(
        "[REPLICATE] Downloading image..."
    )

    image_bytes = _download_image(
        output_url
    )

    print(
        "[REPLICATE] Image downloaded "
        f"({len(image_bytes)} bytes)."
    )

    return image_bytes