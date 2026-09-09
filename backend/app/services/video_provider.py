import os
from pathlib import Path

from .video_generator_v2 import (
    generate_promotional_video_v2,
)


# =========================================================
# PROVIDER CONFIG
# =========================================================

DEFAULT_PROVIDER = os.getenv(
    "VIDEO_PROVIDER",
    "local",
).lower()


# =========================================================
# LOCAL PROVIDER
# =========================================================

def generate_local_video(
    **kwargs,
):

    print(
        "VIDEO PROVIDER: local MoviePy V2"
    )

    return generate_promotional_video_v2(
        **kwargs
    )


# =========================================================
# WAN PROVIDER
# =========================================================

def generate_wan_video(
    **kwargs,
):

    # We will implement this when GPU/API access
    # is configured.

    raise RuntimeError(
        "Wan video provider is not configured."
    )


# =========================================================
# LTX PROVIDER
# =========================================================

def generate_ltx_video(
    **kwargs,
):

    # We will implement this when GPU/API access
    # is configured.

    raise RuntimeError(
        "LTX video provider is not configured."
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
    ).lower()


    # -----------------------------------------------------
    # EXPLICIT LOCAL
    # -----------------------------------------------------

    if selected == "local":

        return generate_local_video(
            **kwargs
        )


    # -----------------------------------------------------
    # EXPLICIT WAN
    # -----------------------------------------------------

    if selected == "wan":

        return generate_wan_video(
            **kwargs
        )


    # -----------------------------------------------------
    # EXPLICIT LTX
    # -----------------------------------------------------

    if selected == "ltx":

        return generate_ltx_video(
            **kwargs
        )


    # -----------------------------------------------------
    # AUTO MODE
    # -----------------------------------------------------

    if selected == "auto":

        providers = [
            (
                "wan",
                generate_wan_video,
            ),

            (
                "ltx",
                generate_ltx_video,
            ),
        ]


        for name, generator in providers:

            try:

                print(
                    f"Trying video provider: {name}"
                )


                return generator(
                    **kwargs
                )


            except Exception as error:

                print(
                    f"{name} unavailable:",
                    repr(error),
                )


        print(
            "AI video providers unavailable. "
            "Falling back to local MoviePy V2."
        )


        return generate_local_video(
            **kwargs
        )


    # -----------------------------------------------------
    # INVALID PROVIDER
    # -----------------------------------------------------

    raise ValueError(
        f"Unknown video provider: {selected}"
    )