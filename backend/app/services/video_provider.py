import os
import shutil
import time
import uuid
from pathlib import Path

import requests

from .video_generator_v2 import (
    generate_promotional_video_v2,
)


REPLICATE_API_URL = "https://api.replicate.com/v1"

POLL_INTERVAL = 3
MAX_WAIT_SECONDS = 600


# =========================================================
# CONFIG
# =========================================================

DEFAULT_PROVIDER = (
    os.getenv(
        "VIDEO_PROVIDER",
        "auto",
    )
    .strip()
    .lower()
)


# =========================================================
# LOCAL MOVIEPY
# =========================================================

def generate_local_video(
    **kwargs,
) -> Path:

    print(
        "[VIDEO] Using local MoviePy V2."
    )

    result = (
        generate_promotional_video_v2(
            **kwargs
        )
    )

    result = Path(result)

    if not result.exists():

        raise RuntimeError(
            "Local video generator did not "
            "create the expected MP4 file."
        )

    return result


# =========================================================
# BUILD VIDEO PROMPT
# =========================================================

def _build_video_prompt(
    business_name: str,
    slogan: str,
    personality,
    marketing_message: str,
) -> str:

    if not personality:

        personality = [
            "professional",
            "modern",
        ]

    personality_text = ", ".join(
        str(item)
        for item in personality[:4]
    )

    prompt = (
        "Premium professional brand reveal animation. "
        f"Brand: {business_name}. "
        f"Brand personality: {personality_text}. "
    )

    if slogan:

        prompt += (
            f"Creative direction inspired by: {slogan}. "
        )

    if marketing_message:

        prompt += (
            "Brand message: "
            f"{marketing_message[:250]}. "
        )

    prompt += (
        "Elegant controlled motion, "
        "premium advertising aesthetic, "
        "clean cinematic composition, "
        "subtle camera movement, "
        "smooth transitions, "
        "professional studio lighting, "
        "maintain the visual identity of the "
        "provided logo, "
        "do not distort the logo, "
        "do not add random text, "
        "do not add watermarks."
    )

    return prompt


# =========================================================
# DOWNLOAD CLOUD VIDEO
# =========================================================

def _download_video(
    url: str,
    output_directory: Path,
) -> Path:

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = (
        f"ai-video-{uuid.uuid4()}.mp4"
    )

    output_path = (
        output_directory
        / filename
    )

    response = requests.get(
        url,
        stream=True,
        timeout=180,
    )

    response.raise_for_status()

    with output_path.open(
        "wb"
    ) as file:

        shutil.copyfileobj(
            response.raw,
            file,
        )

    if (
        not output_path.exists()
        or output_path.stat().st_size < 1000
    ):

        try:
            output_path.unlink(
                missing_ok=True
            )
        except OSError:
            pass

        raise RuntimeError(
            "Downloaded cloud video "
            "is invalid."
        )

    return output_path


# =========================================================
# OUTPUT URL
# =========================================================

def _find_video_url(
    output,
) -> str:

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
                    "video",
                    "output",
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
            "video",
            "output",
        ):

            value = output.get(
                key
            )

            if isinstance(
                value,
                str,
            ):

                return value


    raise RuntimeError(
        "Cloud video provider did not "
        "return a downloadable video URL."
    )


# =========================================================
# REPLICATE CONFIG
# =========================================================

def _replicate_video_configured() -> bool:

    token = (
        os.getenv(
            "REPLICATE_API_TOKEN",
            "",
        )
        .strip()
    )

    model = (
        os.getenv(
            "REPLICATE_VIDEO_MODEL",
            "",
        )
        .strip()
    )

    return bool(
        token and model
    )


# =========================================================
# REPLICATE VIDEO
# =========================================================

def generate_replicate_video(
    **kwargs,
) -> Path:

    token = (
        os.getenv(
            "REPLICATE_API_TOKEN",
            "",
        )
        .strip()
    )

    model = (
        os.getenv(
            "REPLICATE_VIDEO_MODEL",
            "",
        )
        .strip()
        .strip("/")
    )

    if not token:

        raise RuntimeError(
            "REPLICATE_API_TOKEN "
            "is not configured."
        )

    if not model:

        raise RuntimeError(
            "REPLICATE_VIDEO_MODEL "
            "is not configured."
        )


    output_directory = Path(
        kwargs["output_directory"]
    )


    prompt = (
        _build_video_prompt(
            business_name=(
                kwargs.get(
                    "business_name",
                    "Brand",
                )
            ),

            slogan=(
                kwargs.get(
                    "slogan",
                    ""
                )
            ),

            personality=(
                kwargs.get(
                    "personality",
                    []
                )
            ),

            marketing_message=(
                kwargs.get(
                    "marketing_message",
                    ""
                )
            ),
        )
    )


    # -----------------------------------------------------
    # NOTE:
    #
    # This generic implementation sends the prompt.
    #
    # Different Replicate video models may use additional
    # fields such as:
    #
    # image
    # start_image
    # input_image
    #
    # We will adapt this after selecting the actual model.
    # -----------------------------------------------------

    payload = {
        "input": {
            "prompt":
                prompt,
        }
    }


    headers = {
        "Authorization":
            f"Bearer {token}",

        "Content-Type":
            "application/json",

        "Prefer":
            "wait=60",
    }


    endpoint = (
        f"{REPLICATE_API_URL}"
        f"/models/{model}/predictions"
    )


    print(
        "[VIDEO] Requesting Replicate video."
    )

    print(
        f"[VIDEO] Model: {model}"
    )


    response = requests.post(
        endpoint,
        headers=headers,
        json=payload,
        timeout=120,
    )

    if not response.ok:

        raise RuntimeError(
            "Replicate video request failed: "
            f"{response.status_code} "
            f"{response.text[:500]}"
        )


    prediction = response.json()

    started = time.monotonic()


    # =====================================================
    # POLLING
    # =====================================================

    while True:

        status = prediction.get(
            "status",
            "",
        )

        print(
            f"[VIDEO] Replicate status: {status}"
        )


        if status == "succeeded":

            break


        if status in {
            "failed",
            "canceled",
        }:

            raise RuntimeError(
                "Replicate video generation "
                f"{status}: "
                f"{prediction.get('error')}"
            )


        if (
            time.monotonic()
            - started
            > MAX_WAIT_SECONDS
        ):

            raise RuntimeError(
                "Replicate video generation "
                "timed out."
            )


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
                "a video polling URL."
            )


        time.sleep(
            POLL_INTERVAL
        )


        poll_response = requests.get(
            poll_url,

            headers={
                "Authorization":
                    f"Bearer {token}",
            },

            timeout=30,
        )


        poll_response.raise_for_status()


        prediction = (
            poll_response.json()
        )


    # =====================================================
    # DOWNLOAD
    # =====================================================

    video_url = (
        _find_video_url(
            prediction.get(
                "output"
            )
        )
    )


    print(
        "[VIDEO] Downloading cloud video."
    )


    output_path = (
        _download_video(
            video_url,
            output_directory,
        )
    )


    print(
        "[VIDEO] Cloud video ready:",
        output_path,
    )


    return output_path


# =========================================================
# WAN PLACEHOLDER
# =========================================================

def generate_wan_video(
    **kwargs,
) -> Path:

    raise RuntimeError(
        "Direct Wan provider is "
        "not configured."
    )


# =========================================================
# LTX PLACEHOLDER
# =========================================================

def generate_ltx_video(
    **kwargs,
) -> Path:

    raise RuntimeError(
        "Direct LTX provider is "
        "not configured."
    )


# =========================================================
# MAIN ROUTER
# =========================================================

def generate_video(
    provider: str | None = None,
    **kwargs,
) -> Path:

    selected = (
        provider
        or DEFAULT_PROVIDER
        or "auto"
    )

    selected = (
        selected
        .strip()
        .lower()
    )


    # =====================================================
    # LOCAL
    # =====================================================

    if selected == "local":

        return generate_local_video(
            **kwargs
        )


    # =====================================================
    # REPLICATE
    # =====================================================

    if selected == "replicate":

        return generate_replicate_video(
            **kwargs
        )


    # =====================================================
    # WAN
    # =====================================================

    if selected == "wan":

        return generate_wan_video(
            **kwargs
        )


    # =====================================================
    # LTX
    # =====================================================

    if selected == "ltx":

        return generate_ltx_video(
            **kwargs
        )


    # =====================================================
    # AUTO
    # =====================================================

    if selected == "auto":

        errors = []


        # -------------------------------------------------
        # CLOUD FIRST
        # -------------------------------------------------

        if _replicate_video_configured():

            try:

                print(
                    "[VIDEO] Trying cloud provider."
                )


                return generate_replicate_video(
                    **kwargs
                )


            except Exception as error:

                print(
                    "[VIDEO] Cloud provider failed:",
                    repr(error),
                )


                errors.append(
                    f"replicate: {error}"
                )


        else:

            print(
                "[VIDEO] Cloud video "
                "provider is not configured."
            )


        # -------------------------------------------------
        # LOCAL FALLBACK
        # -------------------------------------------------

        try:

            print(
                "[VIDEO] Falling back "
                "to MoviePy."
            )


            return generate_local_video(
                **kwargs
            )


        except Exception as error:

            print(
                "[VIDEO] Local generator failed:",
                repr(error),
            )


            errors.append(
                f"local: {error}"
            )


        raise RuntimeError(
            "All video providers failed. "
            + " | ".join(errors)
        )


    raise ValueError(
        f"Unknown video provider: {selected}"
    )