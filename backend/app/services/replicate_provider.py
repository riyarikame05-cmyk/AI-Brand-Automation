import os
import time
from typing import Any

import requests


REPLICATE_API_URL = "https://api.replicate.com/v1"

REQUEST_TIMEOUT = 90
DOWNLOAD_TIMEOUT = 90
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
        "Professional vector logo symbol. "
        f"Industry: {industry}. "
        f"Creative direction: {concept}. "
        f"Brand style: {style}. "
        f"Logo approach: {logo_type}. "
        f"Geometry inspiration: {shape}. "
        f"Preferred palette: "
        f"{primary}, {secondary}, {accent}. "

        "Create one original, memorable, "
        "minimal brand mark with a strong silhouette. "
        "Use deliberate negative space and "
        "clean geometric construction. "
        "The mark must remain recognizable at small size. "
        "Flat vector design. "
        "Centered composition. "
        "Pure white background. "
        "Crisp edges. "
        "Professional branding agency quality. "

        "Do not include text. "
        "Do not include letters. "
        "Do not include words. "
        "Do not include a company name. "
        "Do not include typography. "
        "Do not include a watermark. "
        "Do not include a signature. "
        "Do not include a mockup. "
        "Do not include stationery. "
        "Do not include a wall. "
        "Do not include a photograph. "
        "Do not include 3D rendering."
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
        f"Professional advertising campaign for "
        f"the {industry} industry. "
        f"{style} visual direction. "

        f"Brand color inspiration: "
        f"{primary}, {secondary}, {accent}. "

        "Premium commercial art direction. "
        "High-end advertising quality. "
        "Intentional composition. "
        "Strong visual hierarchy. "
        "Professional lighting. "
        "Modern brand aesthetic. "
        "Website hero image quality. "
        "Social media campaign quality. "
        "Leave intentional negative space "
        "for marketing copy. "

        "No visible text. "
        "No letters. "
        "No words. "
        "No watermark. "
        "No logo."
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
        purpose
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
# EXTRACT OUTPUT URL
# =========================================================

def _extract_output_url(
    output: Any,
) -> str:

    # Replicate models can return:
    #
    # "https://..."
    #
    # or:
    #
    # ["https://..."]
    #
    # or sometimes structured objects.

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
                ):

                    value = (
                        item.get(key)
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
        ):

            value = (
                output.get(key)
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


    raise RuntimeError(
        "Replicate completed but did not "
        "return a usable image URL."
    )


# =========================================================
# DOWNLOAD IMAGE
# =========================================================

def _download_image(
    url: str,
) -> bytes:

    response = requests.get(
        url,
        timeout=DOWNLOAD_TIMEOUT,
    )

    response.raise_for_status()

    image_bytes = (
        response.content
    )


    if not isinstance(
        image_bytes,
        (bytes, bytearray),
    ):

        raise RuntimeError(
            "Replicate returned invalid image data."
        )


    if len(image_bytes) < 1000:

        raise RuntimeError(
            "Downloaded Replicate image "
            "is too small or invalid."
        )


    return bytes(
        image_bytes
    )


# =========================================================
# REPLICATE GENERATOR
# =========================================================

def generate_replicate_image(
    specification: dict,
    industry: str,
    style: str,
    purpose: str = "campaign",
) -> bytes:

    # =====================================================
    # ENVIRONMENT
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
            "REPLICATE_API_TOKEN "
            "is not configured."
        )


    model = (
        os.getenv(
            "REPLICATE_IMAGE_MODEL",
            "",
        )
        .strip()
    )


    if not model:

        raise RuntimeError(
            "REPLICATE_IMAGE_MODEL "
            "is not configured."
        )


    # Remove accidental whitespace/slashes.

    model = (
        model
        .strip("/")
    )


    # =====================================================
    # PROMPT
    # =====================================================

    prompt = (
        _build_prompt(
            specification=(
                specification
            ),

            industry=(
                industry
            ),

            style=(
                style
            ),

            purpose=(
                purpose
            ),
        )
    )


    print(
        f"[REPLICATE] Purpose: {purpose}"
    )

    print(
        f"[REPLICATE] Model: {model}"
    )


    # =====================================================
    # HEADERS
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


    try:

        response = (
            requests.post(
                endpoint,

                headers=(
                    headers
                ),

                json={
                    "input": {
                        "prompt":
                            prompt,
                    }
                },

                timeout=(
                    REQUEST_TIMEOUT
                ),
            )
        )


        response.raise_for_status()


    except requests.RequestException as error:

        body = ""

        if (
            getattr(
                error,
                "response",
                None
            )
            is not None
        ):

            try:

                body = (
                    error.response.text
                )

            except Exception:

                body = ""


        raise RuntimeError(
            "Replicate prediction request "
            f"failed: {error}. "
            f"{body[:500]}"
        ) from error


    prediction = (
        response.json()
    )


    # =====================================================
    # WAIT FOR RESULT
    # =====================================================

    started = (
        time.monotonic()
    )


    while True:

        status = (
            prediction.get(
                "status",
                ""
            )
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
        # POLL URL
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
                "Replicate did not provide "
                "a prediction polling URL."
            )


        time.sleep(
            POLL_INTERVAL
        )


        try:

            response = (
                requests.get(
                    poll_url,

                    headers={
                        "Authorization":
                            f"Bearer {token}",
                    },

                    timeout=30,
                )
            )


            response.raise_for_status()


            # THIS WAS MISSING IN YOUR FILE.
            prediction = (
                response.json()
            )


        except requests.RequestException as error:

            raise RuntimeError(
                "Could not poll Replicate "
                f"prediction: {error}"
            ) from error


    # =====================================================
    # DOWNLOAD RESULT
    # =====================================================

    output = (
        prediction.get(
            "output"
        )
    )


    output_url = (
        _extract_output_url(
            output
        )
    )


    print(
        "[REPLICATE] Downloading generated image..."
    )


    image_bytes = (
        _download_image(
            output_url
        )
    )


    print(
        "[REPLICATE] Image generation complete."
    )


    return image_bytes