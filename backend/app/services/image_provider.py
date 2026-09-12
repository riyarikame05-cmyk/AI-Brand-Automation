import os

from .flux_provider import generate_flux_symbol
from .replicate_provider import generate_replicate_image


# =========================================================
# CONFIGURATION
# =========================================================

DEFAULT_PROVIDER = os.getenv(
    "IMAGE_PROVIDER",
    "auto",
).lower()


# =========================================================
# LOCAL PROVIDER
# =========================================================

def generate_local_image(**kwargs):
    """
    Reserved for a future fully local/offline image generator.
    """

    raise RuntimeError(
        "Local campaign image provider has not been configured."
    )


# =========================================================
# FLUX / POLLINATIONS PROVIDER
# =========================================================

def generate_flux_image(**kwargs):
    """
    Generate an image using the existing Pollinations/FLUX
    implementation.

    Returns:
        bytes: Raw generated image data.
    """

    specification = kwargs.get(
        "specification",
        {},
    )

    industry = kwargs.get(
        "industry",
        "",
    )

    style = kwargs.get(
        "style",
        "",
    )

    return generate_flux_symbol(
        specification=specification,
        industry=industry,
        style=style,
    )


# =========================================================
# REPLICATE PROVIDER
# =========================================================

def generate_replicate_provider_image(**kwargs):
    """
    Generate an image through Replicate.

    Requires:
        REPLICATE_API_TOKEN
        REPLICATE_IMAGE_MODEL

    Returns:
        bytes: Raw generated image data.
    """

    specification = kwargs.get(
        "specification",
        {},
    )

    industry = kwargs.get(
        "industry",
        "",
    )

    style = kwargs.get(
        "style",
        "",
    )

    return generate_replicate_image(
        specification=specification,
        industry=industry,
        style=style,
    )


# =========================================================
# STUDENT PROVIDER
# =========================================================

def generate_student_image(**kwargs):
    """
    Reserved for a future image-generation service obtained
    specifically through a student benefit.

    GitHub Student itself is not an image-generation API.
    """

    raise RuntimeError(
        "Student image provider is not configured."
    )


# =========================================================
# ROUTER
# =========================================================

def generate_image(
    provider=None,
    **kwargs,
):
    """
    Route image generation to the requested provider.

    Supported providers:
        auto
        replicate
        flux
        local
        student

    `auto` tries providers in priority order and falls back
    when a provider is unavailable.
    """

    selected = (
        provider
        or DEFAULT_PROVIDER
    ).lower()


    # -----------------------------------------------------
    # LOCAL
    # -----------------------------------------------------

    if selected == "local":
        return generate_local_image(
            **kwargs
        )


    # -----------------------------------------------------
    # EXISTING FLUX / POLLINATIONS
    # -----------------------------------------------------

    if selected == "flux":
        return generate_flux_image(
            **kwargs
        )


    # -----------------------------------------------------
    # REPLICATE
    # -----------------------------------------------------

    if selected == "replicate":
        return generate_replicate_provider_image(
            **kwargs
        )


    # -----------------------------------------------------
    # STUDENT
    # -----------------------------------------------------

    if selected == "student":
        return generate_student_image(
            **kwargs
        )


    # -----------------------------------------------------
    # AUTOMATIC FALLBACK
    # -----------------------------------------------------

    if selected == "auto":

        providers = [
            (
                "replicate",
                generate_replicate_provider_image,
            ),
            (
                "flux",
                generate_flux_image,
            ),
        ]

        errors = []

        for name, generator in providers:

            try:
                print(
                    f"Trying image provider: {name}"
                )

                image_bytes = generator(
                    **kwargs
                )

                if not isinstance(
                    image_bytes,
                    (bytes, bytearray),
                ):
                    raise RuntimeError(
                        f"{name} provider returned "
                        "non-binary image data."
                    )

                if len(image_bytes) < 1000:
                    raise RuntimeError(
                        f"{name} provider returned "
                        "invalid image data."
                    )

                print(
                    f"Image provider succeeded: {name}"
                )

                return bytes(image_bytes)

            except Exception as error:

                errors.append(
                    f"{name}: {error}"
                )

                print(
                    f"{name} unavailable:",
                    repr(error),
                )


        # Local provider is the final fallback.
        try:
            print(
                "Trying image provider: local"
            )

            return generate_local_image(
                **kwargs
            )

        except Exception as error:

            errors.append(
                f"local: {error}"
            )


        raise RuntimeError(
            "All image providers failed. "
            + " | ".join(errors)
        )


    # -----------------------------------------------------
    # UNKNOWN PROVIDER
    # -----------------------------------------------------

    raise ValueError(
        f"Unknown image provider: {selected}"
    )