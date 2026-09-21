import os

from .flux_provider import (
    generate_flux_campaign,
    generate_flux_symbol,
)
from .replicate_provider import (
    generate_replicate_image,
)
from .logo_renderer import render_logo


# =========================================================
# CONFIGURATION
# =========================================================

DEFAULT_PROVIDER = (
    os.getenv(
        "IMAGE_PROVIDER",
        "auto",
    )
    .strip()
    .lower()
)


# =========================================================
# VALIDATION
# =========================================================

def _validate_image(
    image_bytes,
    provider_name: str,
) -> bytes:

    if not isinstance(
        image_bytes,
        (bytes, bytearray),
    ):
        raise RuntimeError(
            f"{provider_name} returned "
            "non-binary image data."
        )

    if len(image_bytes) < 1000:
        raise RuntimeError(
            f"{provider_name} returned "
            "invalid image data."
        )

    return bytes(image_bytes)


# =========================================================
# LOCAL PROVIDER
# =========================================================

def generate_local_image(
    **kwargs,
) -> bytes:
    """
    Fully local logo fallback.

    The specification is normally produced by Ollama.
    logo_renderer then creates the actual PNG.

    No cloud API is required.
    """

    purpose = (
        kwargs.get(
            "purpose",
            "symbol",
        )
        .strip()
        .lower()
    )

    if purpose != "symbol":
        raise RuntimeError(
            "Local provider currently supports "
            "logo symbols only."
        )

    specification = kwargs.get(
        "specification",
        {},
    )

    business_name = kwargs.get(
        "business_name",
        "Brand",
    )

    industry = kwargs.get(
        "industry",
        "Business",
    )

    if not specification:
        raise RuntimeError(
            "Logo specification is required "
            "for local rendering."
        )

    print(
        "[IMAGE] Rendering logo locally."
    )

    result = render_logo(
        business_name=business_name,
        industry=industry,
        specification=specification,
    )

    png = result.get("png")

    return _validate_image(
        png,
        "local",
    )


# =========================================================
# FLUX
# =========================================================

def generate_flux_image(
    **kwargs,
) -> bytes:

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

    purpose = (
        kwargs.get(
            "purpose",
            "campaign",
        )
        .strip()
        .lower()
    )

    if purpose == "campaign":

        result = generate_flux_campaign(
            specification=specification,
            industry=industry,
            style=style,
        )

    elif purpose == "symbol":

        result = generate_flux_symbol(
            specification=specification,
            industry=industry,
            style=style,
        )

    else:

        raise ValueError(
            f"Unknown image purpose: {purpose}"
        )

    return _validate_image(
        result,
        "flux",
    )


# =========================================================
# REPLICATE
# =========================================================

def generate_replicate_provider_image(
    **kwargs,
) -> bytes:

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

    purpose = (
        kwargs.get(
            "purpose",
            "campaign",
        )
        .strip()
        .lower()
    )

    result = generate_replicate_image(
        specification=specification,
        industry=industry,
        style=style,
        purpose=purpose,
    )

    return _validate_image(
        result,
        "replicate",
    )


# =========================================================
# CONFIGURATION CHECKS
# =========================================================

def _replicate_configured() -> bool:

    token = (
        os.getenv(
            "REPLICATE_API_TOKEN",
            "",
        )
        .strip()
    )

    model = (
        os.getenv(
            "REPLICATE_IMAGE_MODEL",
            "",
        )
        .strip()
    )

    return bool(
        token and model
    )


# =========================================================
# ROUTER
# =========================================================

def generate_image(
    provider=None,
    **kwargs,
) -> bytes:

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

    # -----------------------------------------------------
    # LOCAL
    # -----------------------------------------------------

    if selected == "local":

        return generate_local_image(
            **kwargs
        )

    # -----------------------------------------------------
    # FLUX
    # -----------------------------------------------------

    if selected == "flux":

        return generate_flux_image(
            **kwargs
        )

    # -----------------------------------------------------
    # REPLICATE
    # -----------------------------------------------------

    if selected == "replicate":

        return (
            generate_replicate_provider_image(
                **kwargs
            )
        )

    # -----------------------------------------------------
    # AUTO
    # -----------------------------------------------------

    if selected == "auto":

        errors = []

        # =============================================
        # 1. REPLICATE
        # =============================================

        if _replicate_configured():

            try:

                print(
                    "[IMAGE] Trying Replicate..."
                )

                result = (
                    generate_replicate_provider_image(
                        **kwargs
                    )
                )

                print(
                    "[IMAGE] Replicate succeeded."
                )

                return result

            except Exception as error:

                print(
                    "[IMAGE] Replicate failed:",
                    repr(error),
                )

                errors.append(
                    f"replicate: {error}"
                )

        else:

            print(
                "[IMAGE] Replicate not configured."
            )

        # =============================================
        # 2. FLUX / POLLINATIONS
        # =============================================

        try:

            print(
                "[IMAGE] Trying FLUX..."
            )

            result = generate_flux_image(
                **kwargs
            )

            print(
                "[IMAGE] FLUX succeeded."
            )

            return result

        except Exception as error:

            print(
                "[IMAGE] FLUX failed:",
                repr(error),
            )

            errors.append(
                f"flux: {error}"
            )

        # =============================================
        # 3. LOCAL FALLBACK
        # =============================================

        try:

            print(
                "[IMAGE] Falling back to local renderer."
            )

            result = generate_local_image(
                **kwargs
            )

            print(
                "[IMAGE] Local renderer succeeded."
            )

            return result

        except Exception as error:

            print(
                "[IMAGE] Local renderer failed:",
                repr(error),
            )

            errors.append(
                f"local: {error}"
            )

        raise RuntimeError(
            "All image providers failed. "
            + " | ".join(errors)
        )

    raise ValueError(
        f"Unknown image provider: {selected}"
    )